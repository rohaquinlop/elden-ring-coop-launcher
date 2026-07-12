"""CLI interface for the Elden Ring Seamless Co-op launcher."""

from __future__ import annotations

import argparse
import pathlib
import sys

from . import __version__
from .config import load_settings
from .constants import ME3_PROFILES_DIR, MOD_DLL, MOD_SETTINGS
from .game import launch_game
from .me3_manager import (
    ensure_me3_installed,
    find_me3_binary,
    get_installed_me3_version,
    get_latest_me3_release,
    install_me3,
    update_me3,
)
from .mod_manager import (
    download_mod,
    ensure_mod_installed,
    get_installed_mod_version,
    get_latest_mod_release,
    update_mod,
)
from .platform_detect import PlatformInfo
from .profile import create_default_profile


def _print_banner() -> None:
    print("=" * 50)
    print("  Elden Ring Seamless Co-op Launcher")
    print(f"  v{__version__}")
    print("=" * 50)
    print()


def cmd_setup(args: argparse.Namespace) -> int:
    """Interactive first-time setup wizard."""
    _print_banner()
    print(">> Setup Wizard")
    print()

    # Step 1: Detect platform
    print("[1/5] Detecting platform...")
    info = PlatformInfo()
    print(info.summary())
    print()

    if not info.game_dir:
        print("ERROR: Elden Ring installation not found!")
        print("  Make sure the game is installed via Steam.")
        if info.is_linux:
            print("  On Linux, ensure Steam is installed and the game is in a Steam library folder.")
        return 1

    print(f"  Found Elden Ring at: {info.game_dir}")
    print()

    # Step 2: Install me3
    print("[2/5] Checking me3 installation...")
    if info.me3_installed:
        version = get_installed_me3_version() or "unknown"
        print(f"  me3 is already installed (v{version})")
    else:
        print("  me3 not found. Installing...")
        try:
            me3_path = install_me3()
            print(f"  Installed me3 to: {me3_path}")
        except Exception as e:
            print(f"  ERROR installing me3: {e}")
            print("  Please install me3 manually: https://me3.help/en/latest/user-guide/installation/")
            return 1
    print()

    # Step 3: Download mod
    print("[3/5] Checking Seamless Co-op mod...")
    mod_dir = info.mod_dir
    if not mod_dir:
        print("  ERROR: Could not determine mod directory!")
        return 1

    dll_path = mod_dir / MOD_DLL
    if dll_path.exists():
        version = get_installed_mod_version(mod_dir) or "unknown"
        print(f"  Mod is already installed (v{version})")
    else:
        print("  Downloading Seamless Co-op mod...")
        try:
            download_mod(mod_dir)
            version = get_installed_mod_version(mod_dir) or "unknown"
            print(f"  Downloaded mod v{version}")
        except Exception as e:
            print(f"  ERROR downloading mod: {e}")
            return 1
    print()

    # Step 4: Configure password
    print("[4/5] Configuring co-op password...")
    settings = load_settings(mod_dir)
    current_pw = settings.get_password()
    if current_pw:
        print(f"  Password is already set: {'*' * len(current_pw)}")
        change = input("  Change password? [y/N]: ").strip().lower()
        if change == "y":
            new_pw = input("  Enter new co-op password: ").strip()
            if new_pw:
                settings.set_password(new_pw)
                settings.save()
                print("  Password updated.")
    else:
        new_pw = input("  Enter co-op password (share with friends): ").strip()
        if new_pw:
            settings.set_password(new_pw)
            settings.save()
            print("  Password set.")
        else:
            print("  No password set. You can set one later with: coop-launcher config password <value>")
    print()

    # Step 5: Create me3 profile
    print("[5/5] Creating me3 profile...")
    try:
        profile_path = create_default_profile(mod_dir, ME3_PROFILES_DIR)
        print(f"  Profile created at: {profile_path}")
    except Exception as e:
        print(f"  ERROR creating profile: {e}")
        return 1
    print()

    print("=" * 50)
    print("  Setup complete!")
    print()
    print("  To launch the game: coop-launcher launch")
    print("  To change password: coop-launcher config password <value>")
    print("  To check status:    coop-launcher status")
    print("=" * 50)
    return 0


def cmd_launch(args: argparse.Namespace) -> int:
    """Launch the game with Seamless Co-op."""
    info = PlatformInfo()

    if not info.game_dir:
        print("ERROR: Elden Ring installation not found!")
        return 1

    # Ensure me3 is installed and get its path
    me3_path = find_me3_binary()
    if not me3_path:
        print("me3 not found. Installing...")
        try:
            me3_path = install_me3()
        except Exception as e:
            print(f"ERROR: Could not install me3: {e}")
            return 1

    # Ensure mod is installed
    mod_dir = info.mod_dir
    if not mod_dir:
        print("ERROR: Could not determine mod directory!")
        return 1

    dll_path = mod_dir / MOD_DLL
    if not dll_path.exists():
        print("Seamless Co-op not found. Downloading...")
        try:
            download_mod(mod_dir)
        except Exception as e:
            print(f"ERROR: Could not download mod: {e}")
            return 1

    # Find or create profile
    profile_path = ME3_PROFILES_DIR / "seamless-coop.me3"
    if not profile_path.exists():
        print("Creating me3 profile...")
        profile_path = create_default_profile(mod_dir, ME3_PROFILES_DIR)

    # Check password
    settings = load_settings(mod_dir)
    if not settings.get_password():
        print("WARNING: No co-op password set!")
        print("  Set one with: coop-launcher config password <value>")
        print()

    # Launch
    extra_args = []
    if getattr(args, "disable_arxan", False):
        extra_args.append("--disable-arxan")

    return launch_game(profile_path, extra_args, me3_path=me3_path)


def cmd_update(args: argparse.Namespace) -> int:
    """Update me3 and/or the mod."""
    _print_banner()
    update_all = not args.me3 and not args.mod
    exit_code = 0

    if args.me3 or update_all:
        print(">> Checking me3 updates...")
        try:
            result = update_me3()
            if result:
                print(f"  Updated me3 to v{result}")
            else:
                version = get_installed_me3_version()
                print(f"  me3 is up to date (v{version or 'unknown'})")
        except Exception as e:
            print(f"  ERROR updating me3: {e}")
            exit_code = 1
        print()

    if args.mod or update_all:
        print(">> Checking mod updates...")
        info = PlatformInfo()
        mod_dir = info.mod_dir
        if not mod_dir:
            print("  ERROR: Mod directory not found!")
            return 1
        try:
            result = update_mod(mod_dir)
            if result:
                print(f"  Updated Seamless Co-op to v{result}")
            else:
                version = get_installed_mod_version(mod_dir)
                print(f"  Mod is up to date (v{version or 'unknown'})")
        except Exception as e:
            print(f"  ERROR updating mod: {e}")
            exit_code = 1

    return exit_code


def cmd_config(args: argparse.Namespace) -> int:
    """Manage configuration."""
    info = PlatformInfo()
    mod_dir = info.mod_dir
    if not mod_dir:
        print("ERROR: Mod directory not found! Run 'coop-launcher setup' first.")
        return 1

    settings = load_settings(mod_dir)

    if args.config_action == "show":
        print(settings.show())
        return 0

    if args.config_action == "password":
        if args.value:
            settings.set_password(args.value)
            settings.save()
            print("Password updated.")
        else:
            pw = settings.get_password()
            if pw:
                print(f"Current password: {pw}")
            else:
                print("No password set.")
        return 0

    if args.config_action == "set":
        if not args.section or not args.key or not args.value:
            print("Usage: coop-launcher config set <section> <key> <value>")
            return 1
        settings.set(args.section, args.key, args.value)
        settings.save()
        print(f"Set [{args.section}] {args.key} = {args.value}")
        return 0

    print("Usage: coop-launcher config {show|password|set}")
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show current status."""
    _print_banner()
    print(">> Platform Info")
    info = PlatformInfo()
    print(info.summary())
    print()

    mod_dir = info.mod_dir
    if mod_dir:
        mod_ver = get_installed_mod_version(mod_dir)
        print(f">> Seamless Co-op: v{mod_ver or 'not installed'}")
        settings = load_settings(mod_dir)
        pw = settings.get_password()
        print(f"   Password:       {'Set (' + '*' * len(pw) + ')' if pw else 'NOT SET'}")
        print(f"   Settings file:  {mod_dir / MOD_SETTINGS}")
        print(f"   DLL present:    {(mod_dir / MOD_DLL).exists()}")
    else:
        print(">> Seamless Co-op: Game directory not found")
    print()

    me3_ver = get_installed_me3_version()
    print(f">> me3:            v{me3_ver or 'not installed'}")

    # Check for updates
    try:
        release = get_latest_me3_release()
        latest_me3 = release["tag_name"].removeprefix("v")
        if me3_ver and me3_ver != latest_me3:
            print(f"   Update available: v{latest_me3}")
    except Exception:
        pass

    try:
        release = get_latest_mod_release()
        latest_mod = release["tag_name"].removeprefix("v")
        mod_ver = get_installed_mod_version(mod_dir) if mod_dir else None
        if mod_ver and mod_ver != latest_mod:
            print(f"   Mod update available: v{latest_mod}")
    except Exception:
        pass

    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Quick launch: setup if needed, then launch."""
    info = PlatformInfo()

    # Auto-setup if needed
    needs_setup = False
    if not info.me3_installed:
        needs_setup = True
    if info.mod_dir and not (info.mod_dir / MOD_DLL).exists():
        needs_setup = True
    if not info.game_dir:
        print("ERROR: Elden Ring not found!")
        return 1

    if needs_setup:
        print("First-time setup required. Running setup...")
        print()
        ret = cmd_setup(args)
        if ret != 0:
            return ret
        print()

    return cmd_launch(args)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="coop-launcher",
        description="Cross-platform launcher for Elden Ring Seamless Co-op",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", help="Command to run")

    # setup
    p_setup = sub.add_parser("setup", help="Interactive first-time setup wizard")

    # launch
    p_launch = sub.add_parser("launch", help="Launch game with Seamless Co-op")
    p_launch.add_argument("--disable-arxan", action="store_true", help="Disable Arxan anti-tamper")

    # run (setup + launch)
    p_run = sub.add_parser("run", help="Setup if needed, then launch")
    p_run.add_argument("--disable-arxan", action="store_true", help="Disable Arxan anti-tamper")

    # update
    p_update = sub.add_parser("update", help="Update me3 and/or the mod")
    p_update.add_argument("--me3", action="store_true", help="Update me3 only")
    p_update.add_argument("--mod", action="store_true", help="Update mod only")

    # config
    p_config = sub.add_parser("config", help="Manage configuration")
    p_config.add_argument("config_action", nargs="?", choices=["show", "password", "set"], default="show")
    p_config.add_argument("section", nargs="?", help="Section name (for 'set')")
    p_config.add_argument("key", nargs="?", help="Key name (for 'set')")
    p_config.add_argument("value", nargs="?", help="Value to set")

    # status
    p_status = sub.add_parser("status", help="Show current status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "setup": cmd_setup,
        "launch": cmd_launch,
        "run": cmd_run,
        "update": cmd_update,
        "config": cmd_config,
        "status": cmd_status,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
