"""Centralized colorization functions for Status and Priority columns."""

from __future__ import annotations

from rich.text import Text

from models import Priority, Status

# ── Display text mappings ────────────────────────────────────────────

STATUS_DISPLAY: dict[Status, str] = {
    Status.TODO: "Todo",
    Status.IN_PROGRESS: "In Progress",
    Status.DONE: "Done",
}

PRIORITY_DISPLAY: dict[Priority, str] = {
    Priority.HIGH: "High",
    Priority.MEDIUM: "Medium",
    Priority.LOW: "Low",
}

# ── Status cycle mapping ─────────────────────────────────────────────

NEXT_STATUS: dict[Status, Status] = {
    Status.TODO: Status.IN_PROGRESS,
    Status.IN_PROGRESS: Status.DONE,
    Status.DONE: Status.IN_PROGRESS,
}

# ── Color functions ──────────────────────────────────────────────────


def colorize_status(status: Status, color_config) -> Text:
    """Return a Rich Text with the status display name colored per config."""
    display = STATUS_DISPLAY.get(status, str(status.value))
    color = color_config.get_status_color(status.value)
    return Text(display, style=color) if color else Text(display)


def colorize_priority(priority: Priority, color_config) -> Text:
    """Return a Rich Text with the priority display name colored per config."""
    display = PRIORITY_DISPLAY.get(priority, str(priority.value))
    color = color_config.get_priority_color(priority.value)
    return Text(display, style=color) if color else Text(display)
