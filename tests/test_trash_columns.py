"""Tests for TrashScreen column order (v1.3.0)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

TRASH_PY = Path(__file__).resolve().parent.parent / "src" / "screens" / "trash.py"


def test_trash_columns_order():
    source = TRASH_PY.read_text()
    expected = 'add_columns("ID", "Category", "Title", "Deleted At", "Expires At")'
    assert expected in source, f"Expected {expected} in trash.py"
