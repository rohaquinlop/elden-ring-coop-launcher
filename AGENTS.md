# AGENTS.md

## What this is

Python CLI that automates Elden Ring Seamless Co-op setup on Windows and Linux. It downloads [me3](https://github.com/garyttierney/me3) (open-source mod loader with Linux/Proton support) and the [Seamless Co-op](https://github.com/yuiamoroll/EldenRingSeamlessCoopRelease) mod from GitHub releases, generates me3 TOML profiles, and launches the game.

The mod itself (`ersc.dll`) is closed-source. This project does NOT contain or modify the mod — it only manages download/install/launch.

## Commands

```bash
uv sync                      # install deps from lockfile
uv run coop-launcher --help
uv run coop-launcher status
uv run coop-launcher setup   # interactive wizard
uv run coop-launcher setup --mod-file <path>  # use local zip
uv run coop-launcher launch
uv run coop-launcher run     # auto-setup + launch
uv run coop-launcher update --mod-file <path> # update from local zip
```

No test suite exists yet. No lint/typecheck commands configured.

## Package manager: uv

This project uses **uv**, not pip. Dependencies are in `pyproject.toml`, lockfile is `uv.lock`.

```bash
uv add <package>       # add dependency
uv sync                # install from lockfile
uv sync --locked       # fail if lockfile is out of date
uv run <command>       # run in project venv
```

The project requires `[build-system]` (hatchling) and `[tool.hatch.build.targets.wheel]` in pyproject.toml. Without them, uv skips creating the `coop-launcher` entry point script, causing "no such file or directory" errors.

## Architecture

Single package: `launcher/`. Entry point is `launcher.cli:main` (registered as `coop-launcher` script in pyproject.toml).

| Module | Responsibility |
|--------|---------------|
| `constants.py` | GitHub repo names, paths, platform flags. Platform-specific paths computed at import time. |
| `platform_detect.py` | Finds Elden Ring via Steam `libraryfolders.vdf` parsing. Uses `vdf` library. |
| `me3_manager.py` | Downloads me3 binaries from GitHub. Linux: tar.gz → `~/.local/share/me3` + symlink to `~/.local/bin/me3`. Windows: zip → `%LOCALAPPDATA%\me3`. |
| `mod_manager.py` | Downloads Seamless Co-op zip from GitHub releases. Extracts to `<game>/Game/SeamlessCoop/`. Writes `VERSION` file. Supports local zip via `install_mod_from_file()` / `update_mod_from_file()`. |
| `profile.py` | Generates `.me3` TOML profile pointing to `ersc.dll`. |
| `config.py` | Reads/writes `ersc_settings.ini` (password). Uses `[PASSWORD]` section — same as the mod. |
| `game.py` | Runs `me3 launch -p <profile>`. |
| `cli.py` | argparse CLI. All commands are `cmd_*` functions. |

## Key technical facts

- me3 profile format is TOML with `profileVersion = "v1"`. The `[[natives]]` section loads DLLs. Paths in profiles must be absolute or relative to the profile file.
- On Linux, me3 handles Proton integration — the Windows DLL loads inside Wine transparently. Steam P2P networking works through Proton, so Windows↔Linux cross-play works.
- `start_online` flag is NOT needed for Seamless Co-op (mod manages its own networking).
- Elden Ring Steam App ID: `1245620`. Game exe: `eldenring.exe`. Mod DLL: `ersc.dll`.
- me3 profiles go in `~/.config/me3/profiles/` (Linux) or `%LOCALAPPDATA%\garyttierney\me3\config\profiles\` (Windows).
- The `vdf` dependency parses Valve Data Format files (Steam config). It's needed for finding non-default Steam library folders.
- `constants.py` has platform branching at module level — `IS_WINDOWS`/`IS_LINUX` and path constants are set on import.

## Conventions

- Python 3.10+ minimum (uses `str | None` union syntax, `from __future__ import annotations`).
- No type stubs for `vdf` — it's untyped.
- `_download_file` is duplicated in `me3_manager.py` and `mod_manager.py` (intentional for now — small codebase).
- `config.py` `ModSettings` only manages the password (`[PASSWORD] cooppassword`). All other settings are left untouched. Uses `RawConfigParser` and targeted text replacement to preserve comments on save.
