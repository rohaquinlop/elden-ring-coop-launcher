"""Constants used across the launcher."""

import pathlib
import sys

# --- GitHub repositories ---
ME3_REPO = "garyttierney/me3"
MOD_REPO = "yuiamoroll/EldenRingSeamlessCoopRelease"
GITHUB_API = "https://api.github.com/repos"
GITHUB_RELEASES = f"{GITHUB_API}/{{repo}}/releases/latest"

# --- Elden Ring ---
ELDEN_RING_APP_ID = 1245620
ELDEN_RING_APP_ID_STR = "1245620"

# --- Mod file names ---
MOD_DLL = "ersc.dll"
MOD_LAUNCHER = "ersc_launcher.exe"
MOD_SETTINGS = "ersc_settings.ini"
MOD_LOCALE_DIR = "locale"
MOD_SAVE_EXT = ".co2"

# --- me3 profile ---
PROFILE_VERSION = "v1"
PROFILE_SAVEFILE = "SeamlessCoop.co2"

# --- Platform-specific paths ---
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
    ME3_CONFIG_DIR = pathlib.Path.home() / "AppData" / "Local" / "garyttierney" / "me3" / "config"
else:
    ME3_CONFIG_DIR = pathlib.Path.home() / ".config" / "me3"

ME3_PROFILES_DIR = ME3_CONFIG_DIR / "profiles"

# --- Steam paths ---
if IS_WINDOWS:
    STEAM_COMMON_DIRS = [
        pathlib.Path("C:/Program Files (x86)/Steam/steamapps"),
        pathlib.Path("D:/Steam/steamapps"),
        pathlib.Path("E:/Steam/steamapps"),
    ]
else:
    STEAM_COMMON_DIRS = [
        pathlib.Path.home() / ".local" / "share" / "Steam" / "steamapps",
        pathlib.Path.home() / ".steam" / "steam" / "steamapps",
    ]

# --- Game manifest ---
STEAM_MANIFEST_NAME = f"appmanifest_{ELDEN_RING_APP_ID}.acf"
GAME_DIR_NAME = "ELDEN RING"
GAME_EXE_NAME = "eldenring.exe"
GAME_SUBPATH = pathlib.Path("common") / GAME_DIR_NAME / "Game"
