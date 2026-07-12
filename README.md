# Elden Ring Seamless Co-op Launcher

Cross-platform launcher for [Seamless Co-op](https://www.nexusmods.com/eldenring/mods/510) (Windows & Linux).

This tool automates the setup and management of:
- **me3** mod loader (supports Linux via Proton)
- **Seamless Co-op** mod download and updates
- **me3 profile** generation
- **Co-op password** configuration

## Quick Start

```bash
# First-time setup (interactive wizard)
coop-launcher setup

# Launch the game
coop-launcher launch

# Or use "run" to auto-setup if needed, then launch
coop-launcher run
```

## Installation

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/rohaquinlop/elden-ring-coop-launcher.git
cd elden-ring-coop-launcher
uv sync
```

Run via the entry point (works after `uv sync`):

```bash
uv run coop-launcher --help
```

## Commands

| Command | Description |
|---------|-------------|
| `coop-launcher setup` | Interactive first-time setup wizard |
| `coop-launcher launch` | Launch game with Seamless Co-op |
| `coop-launcher run` | Setup if needed, then launch |
| `coop-launcher update [--me3] [--mod]` | Update me3 and/or the mod |
| `coop-launcher config show` | Show current configuration |
| `coop-launcher config password [value]` | Get/set co-op password |
| `coop-launcher config set <section> <key> <value>` | Set arbitrary config value |
| `coop-launcher status` | Show current status and check for updates |

## How It Works

1. **Platform detection**: Finds your Elden Ring installation via Steam library folders
2. **me3 management**: Downloads and installs [me3](https://github.com/garyttierney/me3), the open-source mod loader that supports Linux via Proton
3. **Mod management**: Downloads Seamless Co-op from GitHub releases
4. **Profile generation**: Creates a `.me3` TOML profile that tells me3 to load `ersc.dll`
5. **Game launch**: Invokes `me3 launch -p seamless-coop.me3` to start the game with the mod

### Linux

On Linux, me3 handles launching the game through Steam's Proton compatibility layer. The Seamless Co-op Windows DLL (`ersc.dll`) loads natively inside the Wine/Proton environment.

### Windows

On Windows, me3 launches the game directly. The mod DLL loads via standard Windows DLL injection.

## Cross-Platform Multiplayer

Windows and Linux players **can play together** because:
- The mod uses the same DLL (`ersc.dll`) on both platforms
- Steam's P2P networking works transparently through Proton
- The networking protocol is platform-independent

Just make sure everyone:
- Uses the same mod version
- Uses the same game version
- Has the same co-op password in `ersc_settings.ini`

## Configuration

The mod settings are stored in `ersc_settings.ini` inside the SeamlessCoop directory:

```ini
[session]
cooppassword = your_password_here
allow_invaders = 1
death_debuffs = 1
overhead_player_display = 1
skip_splash_screens = 1
```

## Dependencies

- `requests` - HTTP downloads
- `tqdm` - Progress bars
- `vdf` - Steam configuration parsing
