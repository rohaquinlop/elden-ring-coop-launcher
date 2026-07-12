"""Configuration management for ersc_settings.ini."""

from __future__ import annotations

import configparser
import pathlib
import re

from .constants import MOD_SETTINGS

# The section and key the mod uses for the co-op password
_PASSWORD_SECTION = "PASSWORD"
_PASSWORD_KEY = "cooppassword"


class ModSettings:
    """Manager for ersc_settings.ini.

    The mod's INI file has sections like [GAMEPLAY], [SCALING], [PASSWORD], etc.
    We only manage the password — all other settings are left untouched.
    """

    def __init__(self, settings_path: pathlib.Path) -> None:
        self.path = settings_path
        self._parser = configparser.RawConfigParser()
        self._parser.optionxform = str  # preserve key casing
        if settings_path.exists():
            self._parser.read(settings_path, encoding="utf-8")

    def _ensure_password_section(self) -> None:
        if not self._parser.has_section(_PASSWORD_SECTION):
            self._parser.add_section(_PASSWORD_SECTION)
        if not self._parser.has_option(_PASSWORD_SECTION, _PASSWORD_KEY):
            self._parser.set(_PASSWORD_SECTION, _PASSWORD_KEY, "")

    def get(self, section: str, key: str, fallback: str = "") -> str:
        return self._parser.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str) -> None:
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, key, value)

    def get_password(self) -> str:
        self._ensure_password_section()
        return self.get(_PASSWORD_SECTION, _PASSWORD_KEY)

    def set_password(self, password: str) -> None:
        self._ensure_password_section()
        self.set(_PASSWORD_SECTION, _PASSWORD_KEY, password)

    def get_bool(self, section: str, key: str, fallback: bool = True) -> str:
        val = self.get(section, key, "1" if fallback else "0")
        return val.strip() in ("1", "true", "yes", "on")

    def save(self) -> None:
        """Save settings, preserving comments and formatting where possible.

        Does a targeted replacement of cooppassword under [PASSWORD] if the
        file already exists and has that section. Falls back to full rewrite.
        """
        self._ensure_password_section()

        if self.path.exists():
            content = self.path.read_text(encoding="utf-8")
            new_content = self._replace_password_in_text(content)
            if new_content is not None:
                self.path.write_text(new_content, encoding="utf-8")
                return

        # Fallback: full rewrite (new file or section not found)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            self._parser.write(f)

    def _replace_password_in_text(self, content: str) -> str | None:
        """Replace cooppassword value in the [PASSWORD] section of raw text.

        Returns the modified text, or None if the section/key wasn't found.
        """
        password = self._parser.get(_PASSWORD_SECTION, _PASSWORD_KEY, fallback="")

        # Find [PASSWORD] section, then the cooppassword line within it
        lines = content.splitlines(keepends=True)
        in_password_section = False
        found = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                in_password_section = stripped.lower() == f"[{_PASSWORD_SECTION.lower()}]"
                continue
            if in_password_section and stripped.startswith(f"{_PASSWORD_KEY}"):
                # Replace the value: "cooppassword = old" -> "cooppassword = new"
                lines[i] = f"{_PASSWORD_KEY} = {password}\n"
                found = True
                break

        if not found:
            return None

        return "".join(lines)

    def show(self) -> str:
        """Return a human-readable representation of the settings."""
        self._ensure_password_section()
        lines = [f"Settings file: {self.path}"]
        for section in self._parser.sections():
            lines.append(f"\n[{section}]")
            for key, value in self._parser.items(section):
                lines.append(f"  {key} = {value}")
        return "\n".join(lines)


def load_settings(mod_dir: pathlib.Path) -> ModSettings:
    """Load mod settings from the mod directory."""
    return ModSettings(mod_dir / MOD_SETTINGS)
