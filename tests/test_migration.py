"""Tests for src/migration.py — JSON to SQLite migration."""

import sys
import os
import json
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import Priority, Status
from migration import migrate_json_to_sqlite, _convert_task


class TestConvertTask(unittest.TestCase):
    def test_basic_conversion(self):
        item = _convert_task({"title": "Buy milk", "status": "pending", "priority": "high"})
        self.assertEqual(item.title, "Buy milk")
        self.assertEqual(item.status, Status.TODO)
        self.assertEqual(item.priority, Priority.HIGH)

    def test_completed_maps_to_done(self):
        item = _convert_task({"title": "X", "status": "completed"})
        self.assertEqual(item.status, Status.DONE)

    def test_in_progress_mapping(self):
        item = _convert_task({"title": "X", "status": "in_progress"})
        self.assertEqual(item.status, Status.IN_PROGRESS)

    def test_unknown_status_defaults_to_todo(self):
        item = _convert_task({"title": "X", "status": "unknown"})
        self.assertEqual(item.status, Status.TODO)

    def test_missing_status_defaults_to_todo(self):
        item = _convert_task({"title": "X"})
        self.assertEqual(item.status, Status.TODO)

    def test_invalid_priority_defaults_to_medium(self):
        item = _convert_task({"title": "X", "priority": "urgent"})
        self.assertEqual(item.priority, Priority.MEDIUM)

    def test_empty_category_gets_default(self):
        item = _convert_task({"title": "X", "category": ""})
        self.assertEqual(item.category, "未分类")

    def test_missing_category_gets_default(self):
        item = _convert_task({"title": "X"})
        self.assertEqual(item.category, "未分类")

    def test_existing_category_preserved(self):
        item = _convert_task({"title": "X", "category": "frontend"})
        self.assertEqual(item.category, "frontend")

    def test_empty_title_becomes_untitled(self):
        item = _convert_task({"title": ""})
        self.assertEqual(item.title, "Untitled")

    def test_missing_title_becomes_untitled(self):
        item = _convert_task({})
        self.assertEqual(item.title, "Untitled")

    def test_whitespace_title_becomes_untitled(self):
        item = _convert_task({"title": "   "})
        self.assertEqual(item.title, "Untitled")


class TestMigrateJsonToSqlite(unittest.TestCase):
    def _write_json(self, data):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(data, f)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def _tmp_db(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_migrate_basic(self):
        src = self._write_json([
            {"title": "A", "status": "pending", "priority": "high"},
            {"title": "B", "status": "completed"},
        ])
        db = self._tmp_db()
        count = migrate_json_to_sqlite(src, db)
        self.assertEqual(count, 2)

    def test_migrate_empty_list(self):
        src = self._write_json([])
        db = self._tmp_db()
        count = migrate_json_to_sqlite(src, db)
        self.assertEqual(count, 0)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            migrate_json_to_sqlite("/nonexistent.json", ":memory:")

    def test_invalid_json(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        f.write("{not valid json")
        f.close()
        self.addCleanup(os.unlink, f.name)
        with self.assertRaises(json.JSONDecodeError):
            migrate_json_to_sqlite(f.name, ":memory:")

    def test_json_not_list(self):
        src = self._write_json({"key": "value"})
        with self.assertRaises(ValueError):
            migrate_json_to_sqlite(src, ":memory:")

    def test_migrated_data_readable(self):
        src = self._write_json([{"title": "Check", "status": "completed", "priority": "low", "category": "ops"}])
        db = self._tmp_db()
        migrate_json_to_sqlite(src, db)

        from repository import BacklogRepository
        repo = BacklogRepository(db)
        items = repo.list()
        repo.close()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Check")
        self.assertEqual(items[0].status, Status.DONE)
        self.assertEqual(items[0].priority, Priority.LOW)
        self.assertEqual(items[0].category, "ops")


if __name__ == "__main__":
    unittest.main()
