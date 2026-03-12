"""Migration layer: convert old tasks.json to new SQLite database."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

from models import BacklogItem, Priority, Status
from repository import BacklogRepository

# Old status -> new status mapping
_STATUS_MAP: Dict[str, Status] = {
    "pending": Status.TODO,
    "in_progress": Status.IN_PROGRESS,
    "completed": Status.DONE,
}

_DEFAULT_CATEGORY = "未分类"


def migrate_json_to_sqlite(json_path: str, db_path: str) -> int:
    """Migrate tasks from old JSON format to new SQLite database.

    Args:
        json_path: Path to the old tasks.json file.
        db_path: Path to the target SQLite database file.

    Returns:
        Number of tasks migrated.

    Raises:
        FileNotFoundError: If json_path does not exist.
        json.JSONDecodeError: If the JSON file is malformed.
        ValueError: If the JSON content is not a list.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON content must be a list of task objects")

    repo = BacklogRepository(db_path)
    count = 0

    try:
        for entry in data:
            item = _convert_task(entry)
            repo.create(item)
            count += 1
    finally:
        repo.close()

    return count


def _convert_task(task: Dict[str, Any]) -> BacklogItem:
    """Convert a single old-format task dict to a BacklogItem."""
    old_status = task.get("status", "pending")
    status = _STATUS_MAP.get(old_status, Status.TODO)

    old_priority = task.get("priority", "medium")
    try:
        priority = Priority(old_priority)
    except ValueError:
        priority = Priority.MEDIUM

    category = task.get("category", "") or _DEFAULT_CATEGORY

    title = task.get("title", "").strip()
    if not title:
        title = "Untitled"

    return BacklogItem(
        title=title,
        description=task.get("description", ""),
        status=status,
        category=category,
        priority=priority,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migration.py <json_path> [db_path]")
        print("  json_path  - path to old tasks.json")
        print("  db_path    - path to new SQLite DB (default: backlog.db)")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "backlog.db"

    migrated = migrate_json_to_sqlite(src, dst)
    print(f"Migration complete: {migrated} task(s) migrated from {src} to {dst}")
