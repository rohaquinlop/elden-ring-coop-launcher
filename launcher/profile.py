"""me3 profile generation for Seamless Co-op."""

from __future__ import annotations

import pathlib

from .constants import MOD_DLL, PROFILE_SAVEFILE, PROFILE_VERSION


def generate_profile(
    mod_dll_path: pathlib.Path,
    savefile: str = PROFILE_SAVEFILE,
) -> str:
    """Generate a .me3 TOML profile string for Seamless Co-op."""
    # The path in the profile should be relative or absolute
    # Using absolute path is safest across platforms
    dll_str = str(mod_dll_path).replace("\\", "\\\\")

    lines = [
        f'profileVersion = "{PROFILE_VERSION}"',
        f'savefile = "{savefile}"',
        "",
        "[[supports]]",
        'game = "eldenring"',
        "",
        "[[natives]]",
        f"path = '{dll_str}'",
    ]
    return "\n".join(lines) + "\n"


def write_profile(
    profile_path: pathlib.Path,
    mod_dll_path: pathlib.Path,
    savefile: str = PROFILE_SAVEFILE,
) -> pathlib.Path:
    """Write a .me3 profile file for Seamless Co-op."""
    content = generate_profile(mod_dll_path, savefile)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(content, encoding="utf-8")
    return profile_path


def create_default_profile(mod_dir: pathlib.Path, profiles_dir: pathlib.Path) -> pathlib.Path:
    """Create a default Seamless Co-op profile in the me3 profiles directory."""
    dll_path = mod_dir / MOD_DLL
    if not dll_path.exists():
        raise FileNotFoundError(f"Mod DLL not found: {dll_path}")

    profile_path = profiles_dir / "seamless-coop.me3"
    return write_profile(profile_path, dll_path)
