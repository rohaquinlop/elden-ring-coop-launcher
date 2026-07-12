"""Seamless Co-op mod download and update management."""

from __future__ import annotations

import pathlib
import re
import shutil
import tempfile
import zipfile

import requests
from tqdm import tqdm

from .constants import (
    GITHUB_RELEASES,
    MOD_DLL,
    MOD_REPO,
    MOD_SETTINGS,
)


def get_latest_mod_release() -> dict:
    """Fetch the latest Seamless Co-op release info from GitHub."""
    url = GITHUB_RELEASES.format(repo=MOD_REPO)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_installed_mod_version(mod_dir: pathlib.Path) -> str | None:
    """Get the installed mod version from VERSION file or ersc_settings.ini."""
    version_file = mod_dir / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip().removeprefix("v")

    # Try reading from settings ini comment
    settings = mod_dir / MOD_SETTINGS
    if settings.exists():
        content = settings.read_text(encoding="utf-8")
        match = re.search(r"version\s*=\s*(\S+)", content, re.IGNORECASE)
        if match:
            return match.group(1).strip('"').removeprefix("v")

    return None


def _download_file(url: str, dest: pathlib.Path, desc: str = "Downloading") -> None:
    """Download a file with progress bar."""
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    try:
        total = int(resp.headers.get("content-length", 0))
    except (ValueError, TypeError):
        total = 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        with tqdm(total=total, unit="B", unit_scale=True, desc=desc) as pbar:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))


def _find_release_asset(release: dict) -> dict | None:
    """Find the mod zip asset in the release."""
    for asset in release.get("assets", []):
        name = asset["name"].lower()
        if name.endswith(".zip") and "seamless" in name:
            return asset
    # Fallback: any zip
    for asset in release.get("assets", []):
        if asset["name"].lower().endswith(".zip"):
            return asset
    return None


def download_mod(dest_dir: pathlib.Path) -> pathlib.Path:
    """Download and extract the Seamless Co-op mod to dest_dir."""
    release = get_latest_mod_release()
    asset = _find_release_asset(release)

    if not asset:
        raise FileNotFoundError("Could not find mod download asset in release")

    # Download to temp
    tmp_dir = pathlib.Path(tempfile.gettempdir()) / "ersc-mod"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / asset["name"]

    _download_file(asset["browser_download_url"], zip_path, "Downloading Seamless Co-op")

    # Extract
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)

    # The zip may contain a subdirectory (e.g. SeamlessCoop/); flatten it
    seamless_subdir = dest_dir / "SeamlessCoop"
    if seamless_subdir.is_dir():
        for item in seamless_subdir.iterdir():
            dest_item = dest_dir / item.name
            if dest_item.exists():
                if dest_item.is_dir():
                    shutil.rmtree(dest_item)
                else:
                    dest_item.unlink()
            shutil.move(str(item), str(dest_item))
        seamless_subdir.rmdir()

    # Validate the DLL is present after extraction
    dll_path = dest_dir / MOD_DLL
    if not dll_path.exists():
        # Search for it in case the zip had a different structure
        found = list(dest_dir.rglob(MOD_DLL))
        if found:
            # Move it to the expected location
            shutil.move(str(found[0]), str(dll_path))
        else:
            raise FileNotFoundError(
                f"Mod DLL not found after extraction. Expected at: {dll_path}"
            )

    # Write version file
    version = release["tag_name"].removeprefix("v")
    (dest_dir / "VERSION").write_text(version, encoding="utf-8")

    # Clean up
    zip_path.unlink(missing_ok=True)
    shutil.rmtree(tmp_dir, ignore_errors=True)

    return dest_dir


def ensure_mod_installed(mod_dir: pathlib.Path) -> pathlib.Path:
    """Ensure the mod is installed, downloading if necessary."""
    dll = mod_dir / MOD_DLL
    if dll.exists():
        return mod_dir
    return download_mod(mod_dir)


def update_mod(mod_dir: pathlib.Path) -> str | None:
    """Update the mod if a newer version is available. Returns new version or None."""
    current = get_installed_mod_version(mod_dir)
    release = get_latest_mod_release()
    latest = release["tag_name"].removeprefix("v")

    if current and current == latest:
        return None

    # Remove old mod files (keep settings)
    settings_backup = None
    settings_path = mod_dir / MOD_SETTINGS
    if settings_path.exists():
        settings_backup = settings_path.read_bytes()

    for item in mod_dir.iterdir():
        if item.name == MOD_SETTINGS:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    # Download new version
    download_mod(mod_dir)

    # Restore settings
    if settings_backup and not settings_path.exists():
        settings_path.write_bytes(settings_backup)

    return latest
