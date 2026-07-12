"""Configuration management for ersc_settings.ini."""

from __future__ import annotations

import configparser
import pathlib
from typing import Optional

from .constants import MOD_SETTINGS


class ModSettings:
    """Manager for ersc_settings.ini."""

    # Default settings
    DEFAULTS = {
        "session": {
            "cooppassword": "",
            "allow_invaders": "1",
            "death_debuffs": "1",
            "overhead_player_display": "1",
            "skip_splash_screens": "1",
        },
    }

    def __init__(self, settings_path: pathlib.Path) -> None:
        self.path = settings_path
        self._parser = configparser.ConfigParser()
        if settings_path.exists():
            self._parser.read(settings_path, encoding="utf-8")

    def _ensure_defaults(self) -> None:
        for section, values in self.DEFAULTS.items():
            if not self._parser.has_section(section):
                self._parser.add_section(section)
            for key, val in values.items():
                if not self._parser.has_option(section, key):
                    self._parser.set(section, key, val)

    def get(self, section: str, key: str, fallback: str = "") -> str:
        return self._parser.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str) -> None:
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, key, value)

    def get_password(self) -> str:
        return self.get("session", "cooppassword")

    def set_password(self, password: str) -> None:
        self.set("session", "cooppassword", password)

    def get_bool(self, section: str, key: str, fallback: bool = True) -> bool:
        val = self.get(section, key, "1" if fallback else "0")
        return val.strip() in ("1", "true", "yes", "on")

    def save(self) -> None:
        self._ensure_defaults()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            self._parser.write(f)

    def show(self) -> str:
        """Return a human-readable representation of the settings."""
        lines = [f"Settings file: {self.path}"]
        for section in self._parser.sections():
            lines.append(f"\n[{section}]")
            for key, value in self._parser.items(section):
                # Mask password
                display_val = value
                if "password" in key.lower() and value:
                    display_val = "*" * len(value)
                lines.append(f"  {key} = {display_val}")
        return "\n".join(lines)


def load_settings(mod_dir: pathlib.Path) -> ModSettings:
    """Load mod settings from the mod directory."""
    return ModSettings(mod_dir / MOD_SETTINGS)
