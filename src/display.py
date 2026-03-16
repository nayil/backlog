"""Display utilities for table columns."""

from __future__ import annotations


def truncate_title(title: str | None, max_len: int) -> str:
    """Truncate title for display; None or empty returns '-'."""
    if title is None or title == "":
        return "-"
    if len(title) <= max_len:
        return title
    return title[:max_len] + "…"
