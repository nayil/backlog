"""Tests for src/models.py — Status, Priority, BacklogItem."""

import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import BacklogItem, Priority, Status


class TestStatusEnum(unittest.TestCase):
    def test_values(self):
        self.assertEqual(Status.TODO.value, "todo")
        self.assertEqual(Status.IN_PROGRESS.value, "in_progress")
        self.assertEqual(Status.DONE.value, "done")

    def test_from_value(self):
        self.assertIs(Status("todo"), Status.TODO)
        self.assertIs(Status("in_progress"), Status.IN_PROGRESS)

    def test_invalid_value(self):
        with self.assertRaises(ValueError):
            Status("invalid")


class TestPriorityEnum(unittest.TestCase):
    def test_values(self):
        self.assertEqual(Priority.HIGH.value, "high")
        self.assertEqual(Priority.MEDIUM.value, "medium")
        self.assertEqual(Priority.LOW.value, "low")

    def test_invalid_value(self):
        with self.assertRaises(ValueError):
            Priority("critical")


class TestBacklogItem(unittest.TestCase):
    def test_defaults(self):
        item = BacklogItem(title="Test")
        self.assertEqual(item.title, "Test")
        self.assertEqual(item.description, "")
        self.assertEqual(item.status, Status.TODO)
        self.assertEqual(item.priority, Priority.MEDIUM)
        self.assertEqual(item.category, "")
        self.assertIsNone(item.id)
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)

    def test_to_dict(self):
        item = BacklogItem(title="A", description="B", status=Status.DONE, priority=Priority.HIGH, category="cat", id=5)
        d = item.to_dict()
        self.assertEqual(d["id"], 5)
        self.assertEqual(d["title"], "A")
        self.assertEqual(d["status"], "done")
        self.assertEqual(d["priority"], "high")
        self.assertEqual(d["category"], "cat")
        self.assertIn("created_at", d)

    def test_from_dict_full(self):
        now = datetime.now().isoformat()
        data = {"id": 1, "title": "T", "description": "D", "status": "in_progress",
                "priority": "low", "category": "c", "created_at": now, "updated_at": now}
        item = BacklogItem.from_dict(data)
        self.assertEqual(item.status, Status.IN_PROGRESS)
        self.assertEqual(item.priority, Priority.LOW)
        self.assertEqual(item.id, 1)

    def test_from_dict_minimal(self):
        item = BacklogItem.from_dict({"title": "X"})
        self.assertEqual(item.title, "X")
        self.assertEqual(item.status, Status.TODO)
        self.assertEqual(item.priority, Priority.MEDIUM)

    def test_from_dict_invalid_status_fallback(self):
        item = BacklogItem.from_dict({"title": "X", "status": "bogus"})
        self.assertEqual(item.status, Status.TODO)

    def test_from_dict_invalid_priority_fallback(self):
        item = BacklogItem.from_dict({"title": "X", "priority": "bogus"})
        self.assertEqual(item.priority, Priority.MEDIUM)

    def test_from_dict_none_status(self):
        item = BacklogItem.from_dict({"title": "X", "status": None})
        self.assertEqual(item.status, Status.TODO)

    def test_roundtrip(self):
        item = BacklogItem(title="RT", description="round", status=Status.IN_PROGRESS, priority=Priority.LOW, category="test", id=42)
        d = item.to_dict()
        restored = BacklogItem.from_dict(d)
        self.assertEqual(restored.title, item.title)
        self.assertEqual(restored.status, item.status)
        self.assertEqual(restored.priority, item.priority)
        self.assertEqual(restored.id, item.id)

    def test_to_dict_none_timestamps(self):
        item = BacklogItem(title="T")
        item.created_at = None
        item.updated_at = None
        d = item.to_dict()
        self.assertIsNone(d["created_at"])
        self.assertIsNone(d["updated_at"])


class TestBacklogItemSoftDeleteFields(unittest.TestCase):
    """Tests for deleted_at and expires_at fields added in v0.1.0."""

    def test_defaults_deleted_at_none(self):
        item = BacklogItem(title="X")
        self.assertIsNone(item.deleted_at)

    def test_defaults_expires_at_none(self):
        item = BacklogItem(title="X")
        self.assertIsNone(item.expires_at)

    def test_to_dict_includes_deleted_at_none(self):
        item = BacklogItem(title="X")
        d = item.to_dict()
        self.assertIn("deleted_at", d)
        self.assertIsNone(d["deleted_at"])

    def test_to_dict_includes_expires_at_none(self):
        item = BacklogItem(title="X")
        d = item.to_dict()
        self.assertIn("expires_at", d)
        self.assertIsNone(d["expires_at"])

    def test_to_dict_deleted_at_iso_string(self):
        now = datetime.now()
        item = BacklogItem(title="X", deleted_at=now)
        d = item.to_dict()
        self.assertEqual(d["deleted_at"], now.isoformat())

    def test_to_dict_expires_at_iso_string(self):
        now = datetime.now()
        item = BacklogItem(title="X", expires_at=now)
        d = item.to_dict()
        self.assertEqual(d["expires_at"], now.isoformat())

    def test_from_dict_parses_deleted_at(self):
        now = datetime.now()
        item = BacklogItem.from_dict({"title": "X", "deleted_at": now.isoformat()})
        self.assertIsNotNone(item.deleted_at)
        self.assertAlmostEqual(item.deleted_at.timestamp(), now.timestamp(), places=3)

    def test_from_dict_parses_expires_at(self):
        now = datetime.now()
        item = BacklogItem.from_dict({"title": "X", "expires_at": now.isoformat()})
        self.assertIsNotNone(item.expires_at)
        self.assertAlmostEqual(item.expires_at.timestamp(), now.timestamp(), places=3)

    def test_from_dict_missing_deleted_at_defaults_none(self):
        item = BacklogItem.from_dict({"title": "X"})
        self.assertIsNone(item.deleted_at)

    def test_from_dict_missing_expires_at_defaults_none(self):
        item = BacklogItem.from_dict({"title": "X"})
        self.assertIsNone(item.expires_at)

    def test_from_dict_null_deleted_at(self):
        item = BacklogItem.from_dict({"title": "X", "deleted_at": None})
        self.assertIsNone(item.deleted_at)

    def test_from_dict_null_expires_at(self):
        item = BacklogItem.from_dict({"title": "X", "expires_at": None})
        self.assertIsNone(item.expires_at)

    def test_roundtrip_with_soft_delete_fields(self):
        now = datetime.now()
        item = BacklogItem(title="RT", deleted_at=now, expires_at=now)
        d = item.to_dict()
        restored = BacklogItem.from_dict(d)
        self.assertAlmostEqual(restored.deleted_at.timestamp(), now.timestamp(), places=3)
        self.assertAlmostEqual(restored.expires_at.timestamp(), now.timestamp(), places=3)


if __name__ == "__main__":
    unittest.main()
