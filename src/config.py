"""Persistent configuration for Backlog Manager."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR: Path = Path.home() / ".backlog"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"
DEFAULT_THEME: str = "textual-dark"


class BacklogConfig:
    """Manages persistent configuration stored in ~/.backlog/config.json."""

    def __init__(self, config_path: str | None = None) -> None:
        if config_path:
            self._config_file = Path(config_path)
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            self._config_file = CONFIG_FILE

    def _load(self) -> dict:
        try:
            with self._config_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict) -> None:
        try:
            with self._config_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            import sys
            print(f"[backlog] warning: failed to save config: {exc}", file=sys.stderr)

    def get_theme(self) -> str:
        """Return saved theme name, falling back to DEFAULT_THEME."""
        data = self._load()
        return data.get("theme", DEFAULT_THEME)

    def set_theme(self, name: str) -> None:
        """Persist theme name to config.json."""
        data = self._load()
        data["theme"] = name
        self._save(data)


def load_config() -> dict:
    return BacklogConfig()._load()


def save_config(config: dict) -> None:
    BacklogConfig()._save(config)


def get_theme() -> str:
    return BacklogConfig().get_theme()


def set_theme(name: str) -> None:
    BacklogConfig().set_theme(name)
