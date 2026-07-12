"""Game launching via me3."""

from __future__ import annotations

import pathlib
import subprocess
import sys

from .constants import ELDEN_RING_APP_ID_STR, IS_LINUX


def launch_game(
    profile_path: pathlib.Path,
    extra_args: list[str] | None = None,
) -> int:
    """Launch Elden Ring with Seamless Co-op via me3.

    Args:
        profile_path: Path to the .me3 profile file.
        extra_args: Additional arguments to pass to me3.

    Returns:
        Process exit code.
    """
    cmd = ["me3", "launch", "-p", str(profile_path)]
    if extra_args:
        cmd.extend(extra_args)

    print(f"Launching: {' '.join(cmd)}")
    print()

    # On Linux, we need to ensure Steam is running
    if IS_LINUX:
        _ensure_steam_running()

    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return 130
    except FileNotFoundError:
        print("Error: 'me3' not found on PATH. Please install me3 first.")
        print("  Run: coop-launcher setup")
        return 1


def _ensure_steam_running() -> None:
    """Check if Steam is running on Linux, warn if not."""
    import shutil
    if shutil.which("steam"):
        try:
            result = subprocess.run(
                ["pgrep", "-x", "steam"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                print("Warning: Steam does not appear to be running.")
                print("  me3 will attempt to launch Steam automatically.")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass


def launch_game_direct(exe_path: pathlib.Path) -> int:
    """Launch the game executable directly (without me3, for vanilla play)."""
    if IS_LINUX:
        # Use Steam URL protocol to launch with Proton
        import webbrowser
        url = f"steam://rungameid/{ELDEN_RING_APP_ID_STR}"
        print(f"Launching via Steam: {url}")
        webbrowser.open(url)
        return 0
    else:
        print(f"Launching: {exe_path}")
        result = subprocess.run([str(exe_path)])
        return result.returncode
