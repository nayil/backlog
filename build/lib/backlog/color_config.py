"""User-configurable color settings for Status and Priority columns."""

from __future__ import annotations

import re

from config import BacklogConfig

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ColorConfig:
    """Manages per-enum-value text colors for Status and Priority.

    Delegates file I/O to ``BacklogConfig`` (composition) to avoid
    two classes independently writing to the same JSON file.
    """

    DEFAULT_STATUS_COLORS: dict[str, str] = {
        "todo": "#61AFEF",
        "in_progress": "#E5C07B",
        "done": "#98C379",
    }

    DEFAULT_PRIORITY_COLORS: dict[str, str] = {
        "high": "#E06C75",
        "medium": "#E5C07B",
        "low": "#98C379",
    }

    def __init__(self, config_path: str | None = None) -> None:
        self._bc = BacklogConfig(config_path) if config_path else BacklogConfig()
        self._status: dict[str, str] = {}
        self._priority: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        data = self._bc._load()
        self._status = self._validated(
            data.get("status_colors", {}), set(self.DEFAULT_STATUS_COLORS)
        )
        self._priority = self._validated(
            data.get("priority_colors", {}), set(self.DEFAULT_PRIORITY_COLORS)
        )

    @staticmethod
    def _validated(mapping: object, known_keys: set[str] | None = None) -> dict[str, str]:
        if not isinstance(mapping, dict):
            return {}
        return {k: v for k, v in mapping.items()
                if isinstance(v, str) and _HEX_RE.match(v)
                and (known_keys is None or k in known_keys)}

    def get_status_color(self, status_value: str) -> str:
        return self._status.get(
            status_value,
            self.DEFAULT_STATUS_COLORS.get(status_value, ""),
        )

    def get_priority_color(self, priority_value: str) -> str:
        return self._priority.get(
            priority_value,
            self.DEFAULT_PRIORITY_COLORS.get(priority_value, ""),
        )

    def set_status_color(self, status_value: str, color: str) -> None:
        if not _HEX_RE.match(color):
            raise ValueError(f"Invalid hex color: {color!r}")
        data = self._bc._load()
        colors = data.setdefault("status_colors", {})
        colors[status_value] = color
        self._bc._save(data)
        self._status[status_value] = color

    def set_priority_color(self, priority_value: str, color: str) -> None:
        if not _HEX_RE.match(color):
            raise ValueError(f"Invalid hex color: {color!r}")
        data = self._bc._load()
        colors = data.setdefault("priority_colors", {})
        colors[priority_value] = color
        self._bc._save(data)
        self._priority[priority_value] = color
