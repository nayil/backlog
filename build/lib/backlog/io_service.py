"""IO service for exporting and importing BacklogItem data."""

from __future__ import annotations

import csv
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import BacklogItem
    from repository import BacklogRepository

CSV_FIELDS = [
    "id",
    "title",
    "description",
    "status",
    "category",
    "priority",
    "created_at",
    "updated_at",
    "deleted_at",
    "expires_at",
]


def export_json(items: list[BacklogItem], file_path: str) -> int:
    """Export a list of BacklogItems to a JSON file. Returns the number of items exported."""
    data = [item.to_dict() for item in items]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(data)


def export_csv(items: list[BacklogItem], file_path: str) -> int:
    """Export a list of BacklogItems to a CSV file. Returns the number of items exported."""
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in items:
            writer.writerow(item.to_dict())
    return len(items)


def _should_skip(data: dict) -> bool:
    """Return True if the record should be skipped during import."""
    title = data.get("title")
    if not (title is not None and str(title).strip()):
        return True
    deleted_at = data.get("deleted_at")
    expires_at = data.get("expires_at")
    if (deleted_at is not None and str(deleted_at).strip()) or \
       (expires_at is not None and str(expires_at).strip()):
        return True
    return False


def _build_item_without_id(data: dict) -> BacklogItem:
    """Build a BacklogItem from dict, ignoring the original id field."""
    from models import BacklogItem

    clean = dict(data)
    clean.pop("id", None)
    clean.pop("deleted_at", None)
    clean.pop("expires_at", None)
    return BacklogItem.from_dict(clean)


def import_json(file_path: str, repo: BacklogRepository) -> tuple[int, int]:
    """Import BacklogItems from a JSON file into the repository.

    Returns (imported_count, skipped_count). Original ids are ignored; new ids
    are assigned by the repository.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError("JSON file must contain a top-level list of records")

    imported = 0
    skipped = 0
    for record in records:
        if _should_skip(record):
            skipped += 1
            continue
        item = _build_item_without_id(record)
        repo.create(item)
        imported += 1

    return imported, skipped


def import_csv(file_path: str, repo: BacklogRepository) -> tuple[int, int]:
    """Import BacklogItems from a CSV file into the repository.

    Returns (imported_count, skipped_count). Original ids are ignored; new ids
    are assigned by the repository. Extra columns in the CSV are silently ignored.
    """
    imported = 0
    skipped = 0
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if _should_skip(row):
                skipped += 1
                continue
            item = _build_item_without_id(dict(row))
            repo.create(item)
            imported += 1

    return imported, skipped
