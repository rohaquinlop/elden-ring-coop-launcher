"""Platform detection: OS, Steam install, game directory, Proton."""

from __future__ import annotations

import pathlib
import shutil
import vdf
from typing import Optional

from .constants import (
    ELDEN_RING_APP_ID,
    ELDEN_RING_APP_ID_STR,
    GAME_SUBPATH,
    IS_LINUX,
    IS_WINDOWS,
    STEAM_COMMON_DIRS,
    STEAM_MANIFEST_NAME,
)


def find_steam_library_folders() -> list[pathlib.Path]:
    """Find all Steam library folders."""
    libraries: list[pathlib.Path] = []
    for base in STEAM_COMMON_DIRS:
        if base.parent.exists():
            libraries.append(base)

    # Parse libraryfolders.vdf for additional libraries
    for base in list(libraries):
        vdf_path = base / "libraryfolders.vdf"
        if vdf_path.exists():
            try:
                data = vdf.loads(vdf_path.read_text(encoding="utf-8"))
                for entry in data.get("libraryfolders", {}).values():
                    if isinstance(entry, dict) and "path" in entry:
                        lib = pathlib.Path(entry["path"]) / "steamapps"
                        if lib not in libraries and lib.exists():
                            libraries.append(lib)
            except Exception:
                pass

    return libraries


def find_elden_ring_dir() -> Optional[pathlib.Path]:
    """Find the Elden Ring game installation directory."""
    for lib in find_steam_library_folders():
        candidate = lib / "common" / "ELDEN RING"
        manifest = lib / STEAM_MANIFEST_NAME
        if candidate.is_dir() and (candidate / "Game" / "eldenring.exe").exists():
            return candidate
        if manifest.exists():
            # Manifest exists but game dir might be elsewhere
            try:
                data = vdf.loads(manifest.read_text(encoding="utf-8"))
                installdir = data.get("AppState", {}).installdir
                if installdir:
                    candidate = lib / "common" / installdir
                    if candidate.is_dir() and (candidate / "Game" / "eldenring.exe").exists():
                        return candidate
            except Exception:
                pass
    return None


def find_proton_version(game_dir: pathlib.Path) -> Optional[str]:
    """Find the Proton version configured for Elden Ring in Steam."""
    if not IS_LINUX:
        return None

    # Check Steam's config for the compatibility tool
    for lib in find_steam_library_folders():
        config_path = lib.parent / "config" / "config.vdf"
        if config_path.exists():
            try:
                data = vdf.loads(config_path.read_text(encoding="utf-8"))
                installs = data.get("InstallConfigStore", {}).get("Software", {}).get("Valve", {}).get("Steam", {})
                compat = installs.get("CompatToolMapping", {})
                game_entry = compat.get(ELDEN_RING_APP_ID_STR, {})
                if "name" in game_entry:
                    return game_entry["name"]
            except Exception:
                pass

    # Check localconfig.vdf
    local_config = pathlib.Path.home() / ".local" / "share" / "Steam" / "userdata"
    if local_config.exists():
        for user_dir in local_config.iterdir():
            config = user_dir / "config" / "localconfig.vdf"
            if config.exists():
                try:
                    data = vdf.loads(config.read_text(encoding="utf-8"))
                    # This is more complex, but the above should work for most cases
                except Exception:
                    pass

    return None


def get_game_exe_path() -> Optional[pathlib.Path]:
    """Get the full path to eldenring.exe."""
    game_dir = find_elden_ring_dir()
    if game_dir:
        exe = game_dir / "Game" / "eldenring.exe"
        if exe.exists():
            return exe
    return None


def get_mod_dir() -> Optional[pathlib.Path]:
    """Get the SeamlessCoop mod directory inside the game folder."""
    game_dir = find_elden_ring_dir()
    if game_dir:
        mod_dir = game_dir / "Game" / "SeamlessCoop"
        return mod_dir
    return None


def check_me3_installed() -> bool:
    """Check if me3 is available (on PATH or at known install location)."""
    from .me3_manager import find_me3_binary
    return find_me3_binary() is not None


def get_me3_binary_path() -> Optional[str]:
    """Get the path to the me3 binary."""
    from .me3_manager import find_me3_binary
    p = find_me3_binary()
    return str(p) if p else None


class PlatformInfo:
    """Container for platform detection results."""

    def __init__(self) -> None:
        self.is_windows = IS_WINDOWS
        self.is_linux = IS_LINUX
        self.game_dir = find_elden_ring_dir()
        self.game_exe = get_game_exe_path()
        self.mod_dir = get_mod_dir()
        self.me3_installed = check_me3_installed()
        self.me3_path = get_me3_binary_path()
        self.proton_version = find_proton_version(self.game_dir) if self.game_dir else None

    def summary(self) -> str:
        lines = [
            f"Platform:       {'Windows' if self.is_windows else 'Linux'}",
            f"Game directory: {self.game_dir or 'NOT FOUND'}",
            f"Game executable:{self.game_exe or 'NOT FOUND'}",
            f"Mod directory:  {self.mod_dir or 'NOT FOUND'}",
            f"me3 installed:  {'Yes (' + self.me3_path + ')' if self.me3_installed else 'No'}",
        ]
        if self.is_linux:
            lines.append(f"Proton version: {self.proton_version or 'Default'}")
        return "\n".join(lines)
