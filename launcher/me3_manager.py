"""me3 mod loader installation and update management."""

from __future__ import annotations

import os
import pathlib
import shutil
import stat
import subprocess
import tarfile
import zipfile

import requests
from tqdm import tqdm

from .constants import GITHUB_RELEASES, IS_LINUX, IS_WINDOWS, ME3_CONFIG_DIR, ME3_REPO


def get_latest_me3_release() -> dict:
    """Fetch the latest me3 release info from GitHub."""
    url = GITHUB_RELEASES.format(repo=ME3_REPO)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def find_me3_binary() -> pathlib.Path | None:
    """Find me3 binary. Checks PATH first, then known install locations."""
    # Check PATH
    path = shutil.which("me3")
    if path:
        return pathlib.Path(path)

    # Fallback: known install locations
    candidates: list[pathlib.Path] = []
    if IS_LINUX:
        candidates.append(pathlib.Path.home() / ".local" / "bin" / "me3")
    elif IS_WINDOWS:
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidates.append(pathlib.Path(local_app_data) / "me3" / "me3.exe")

    for c in candidates:
        if c.exists() and c.is_file():
            return c

    return None


def get_installed_me3_version() -> str | None:
    """Get the currently installed me3 version."""
    me3_bin = find_me3_binary()
    if not me3_bin:
        return None
    try:
        result = subprocess.run(
            [str(me3_bin), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Output like "me3 0.11.0"
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                return parts[-1].lstrip("v")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _download_file(url: str, dest: pathlib.Path, desc: str = "Downloading") -> None:
    """Download a file with progress bar."""
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        with tqdm(total=total, unit="B", unit_scale=True, desc=desc) as pbar:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))


def _find_asset(release: dict, suffix: str) -> dict | None:
    """Find a release asset matching the given suffix."""
    for asset in release.get("assets", []):
        name = asset["name"].lower()
        if name.endswith(suffix.lower()):
            return asset
    return None


def install_me3_linux(release: dict) -> pathlib.Path:
    """Install me3 on Linux from GitHub release."""
    asset = _find_asset(release, "linux-amd64.tar.gz")
    if not asset:
        # Fallback: try the installer script
        return _install_me3_linux_script()

    download_dir = pathlib.Path("/tmp") / "me3-install"
    download_dir.mkdir(parents=True, exist_ok=True)
    archive_path = download_dir / asset["name"]

    _download_file(asset["browser_download_url"], archive_path, "Downloading me3")

    # Extract to ~/.local/share/me3
    install_dir = pathlib.Path.home() / ".local" / "share" / "me3"
    install_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=install_dir, filter="data")

    # Find the me3 binary and symlink to ~/.local/bin
    me3_bin = None
    for p in install_dir.rglob("me3"):
        if p.is_file() and os.access(p, os.X_OK):
            me3_bin = p
            break

    if not me3_bin:
        # Try finding bin/me3
        me3_bin = install_dir / "bin" / "me3"
        if not me3_bin.exists():
            raise FileNotFoundError("Could not find me3 binary in archive")

    # Make executable
    me3_bin.chmod(me3_bin.stat().st_mode | stat.S_IEXEC)

    # Symlink to ~/.local/bin
    local_bin = pathlib.Path.home() / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)
    link = local_bin / "me3"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(me3_bin)

    # Clean up
    archive_path.unlink(missing_ok=True)
    download_dir.rmdir()

    _warn_path_if_needed(me3_bin)

    return me3_bin


def _install_me3_linux_script() -> pathlib.Path:
    """Install me3 on Linux using the official installer script."""
    result = subprocess.run(
        [
            "bash", "-c",
            "curl --proto '=https' --tlsv1.2 -sSfL "
            "https://github.com/garyttierney/me3/releases/latest/download/installer.sh | sh",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"me3 installer failed: {result.stderr}")

    me3_path = pathlib.Path.home() / ".local" / "bin" / "me3"
    if not me3_path.exists():
        raise FileNotFoundError("me3 installation completed but binary not found")
    return me3_path


def install_me3_windows(release: dict) -> pathlib.Path:
    """Install me3 on Windows from GitHub release."""
    asset = _find_asset(release, "windows-amd64.zip")
    if not asset:
        raise FileNotFoundError("Could not find Windows me3 release asset")

    download_dir = pathlib.Path(os.environ.get("TEMP", "/tmp")) / "me3-install"
    download_dir.mkdir(parents=True, exist_ok=True)
    archive_path = download_dir / asset["name"]

    _download_file(asset["browser_download_url"], archive_path, "Downloading me3")

    # Extract to %LOCALAPPDATA%\me3
    install_dir = pathlib.Path(os.environ["LOCALAPPDATA"]) / "me3"
    install_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(install_dir)

    # Find me3.exe
    me3_exe = install_dir / "me3.exe"
    if not me3_exe.exists():
        for p in install_dir.rglob("me3.exe"):
            me3_exe = p
            break

    if not me3_exe.exists():
        raise FileNotFoundError("Could not find me3.exe in archive")

    # Clean up
    archive_path.unlink(missing_ok=True)

    return me3_exe


def install_me3() -> pathlib.Path:
    """Install me3 for the current platform."""
    release = get_latest_me3_release()
    if IS_LINUX:
        return install_me3_linux(release)
    elif IS_WINDOWS:
        return install_me3_windows(release)
    else:
        raise RuntimeError(f"Unsupported platform: {os.name}")


def ensure_me3_installed() -> pathlib.Path:
    """Ensure me3 is installed, installing if necessary. Returns path to binary."""
    me3_path = find_me3_binary()
    if me3_path:
        return me3_path
    return install_me3()


def update_me3() -> str | None:
    """Update me3 if a newer version is available. Returns new version or None."""
    current = get_installed_me3_version()
    release = get_latest_me3_release()
    latest = release["tag_name"].lstrip("v")

    if current and current == latest:
        return None

    install_me3()
    return latest


def _warn_path_if_needed(me3_bin: pathlib.Path) -> None:
    """Warn if ~/.local/bin is not on PATH (Linux)."""
    if not IS_LINUX:
        return
    local_bin = str(pathlib.Path.home() / ".local" / "bin")
    path_env = os.environ.get("PATH", "")
    if local_bin not in path_env.split(":"):
        print(f"  NOTE: {local_bin} is not on your PATH.")
        print(f"  me3 binary is at: {me3_bin}")
        print(f"  Add to your shell profile: export PATH=\"$HOME/.local/bin:$PATH\"")
