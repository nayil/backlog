"""Persistent configuration for Backlog Manager."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR: Path = Path.home() / ".backlog"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"


class BacklogConfig:
    """Manages persistent configuration stored in ~/.backlog/config.json."""

    DEFAULT_TITLE_TRUNCATE_LENGTH = 35

    def __init__(self, config_path: str | None = None) -> None:
        if config_path:
            self._config_file = Path(config_path)
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            self._config_file = CONFIG_FILE

    def get_title_truncate_length(self) -> int:
        """Return title_truncate_length from config; invalid values fall back to 35."""
        data = self._load()
        val = data.get("title_truncate_length", self.DEFAULT_TITLE_TRUNCATE_LENGTH)
        if not isinstance(val, int) or val <= 0:
            return self.DEFAULT_TITLE_TRUNCATE_LENGTH
        return val

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


def load_config() -> dict:
    return BacklogConfig()._load()


def save_config(config: dict) -> None:
    BacklogConfig()._save(config)
