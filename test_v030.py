"""Tests for v0.3.0 features: IO Service, Repository, and App structure."""

import ast
import csv
import json
import os
import sys
import tempfile
import unittest

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


class TestExportJson(unittest.TestCase):
    def setUp(self):
        from models import BacklogItem
        from repository import BacklogRepository
        import io_service as ios

        self.ios = ios
        self.BacklogItem = BacklogItem
        self.tmp = tempfile.mktemp(suffix=".json")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def _make_item(self, title="Test Item"):
        return self.BacklogItem(title=title, description="desc")

    def test_export_json_normal(self):
        """export_json: normal list, returns correct count and writes valid JSON."""
        items = [self._make_item("A"), self._make_item("B")]
        count = self.ios.export_json(items, self.tmp)
        self.assertEqual(count, 2)
        with open(self.tmp, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "A")
        self.assertEqual(data[1]["title"], "B")

    def test_export_json_empty(self):
        """export_json: empty list, returns 0 and writes []."""
        count = self.ios.export_json([], self.tmp)
        self.assertEqual(count, 0)
        with open(self.tmp, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, [])


class TestExportCsv(unittest.TestCase):
    def setUp(self):
        from models import BacklogItem
        import io_service as ios

        self.ios = ios
        self.BacklogItem = BacklogItem
        self.tmp = tempfile.mktemp(suffix=".csv")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def _make_item(self, title="Test Item"):
        return self.BacklogItem(title=title, description="desc")

    def test_export_csv_normal(self):
        """export_csv: normal list, returns count and writes CSV with header."""
        items = [self._make_item("X"), self._make_item("Y")]
        count = self.ios.export_csv(items, self.tmp)
        self.assertEqual(count, 2)
        with open(self.tmp, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "X")
        self.assertEqual(rows[1]["title"], "Y")

    def test_export_csv_empty(self):
        """export_csv: empty list, returns 0 and writes only header."""
        count = self.ios.export_csv([], self.tmp)
        self.assertEqual(count, 0)
        with open(self.tmp, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(rows, [])


class TestImportJson(unittest.TestCase):
    def setUp(self):
        import io_service as ios
        from repository import BacklogRepository

        self.ios = ios
        self.BacklogRepository = BacklogRepository
        self.db_tmp = tempfile.mktemp(suffix=".db")
        self.repo = BacklogRepository(db_path=self.db_tmp)
        self.json_tmp = tempfile.mktemp(suffix=".json")

    def tearDown(self):
        self.repo.close()
        for f in [self.db_tmp, self.json_tmp]:
            if os.path.exists(f):
                os.remove(f)

    def _write_json(self, data):
        with open(self.json_tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_import_json_normal(self):
        """import_json: valid list, records without deleted/expires dates are imported.

        Note: due to BUG (str(None)='None' truthy), null JSON values for deleted_at/expires_at
        cause records to be skipped. This test uses empty strings as a workaround to verify
        the core import logic works. The bug is separately documented in test_import_json_null_dates_bug.
        """
        records = [
            {"id": 999, "title": "Task A", "description": "desc A", "status": "todo",
             "category": "", "priority": "medium", "created_at": "2026-01-01T00:00:00",
             "updated_at": "2026-01-01T00:00:00", "deleted_at": "", "expires_at": ""},
            {"id": 888, "title": "Task B", "description": "desc B", "status": "in_progress",
             "category": "work", "priority": "high", "created_at": "2026-01-02T00:00:00",
             "updated_at": "2026-01-02T00:00:00", "deleted_at": "", "expires_at": ""},
        ]
        self._write_json(records)
        imported, skipped = self.ios.import_json(self.json_tmp, self.repo)
        self.assertEqual(imported, 2)
        self.assertEqual(skipped, 0)

    def test_import_json_null_dates_fixed(self):
        """FIXED: import_json correctly imports records with deleted_at=null/None.

        After the DEV-6-1 fix, None values for deleted_at/expires_at are treated as
        "no date set" (not deleted/expired), so records are correctly imported.
        JSON round-trip works as expected.
        """
        records = [
            {"id": 1, "title": "Bug Victim", "description": "", "status": "todo",
             "category": "", "priority": "medium", "created_at": "2026-01-01T00:00:00",
             "updated_at": "2026-01-01T00:00:00", "deleted_at": None, "expires_at": None},
        ]
        self._write_json(records)
        imported, skipped = self.ios.import_json(self.json_tmp, self.repo)
        # FIXED: deleted_at=None → not deleted → record is imported
        self.assertEqual(imported, 1, "Record with deleted_at=None should be imported")
        self.assertEqual(skipped, 0, "Record with deleted_at=None should not be skipped")

    def test_import_json_id_reassigned(self):
        """import_json: original id is ignored; repo assigns new id."""
        records = [
            {"id": 9999, "title": "Reassign Me", "description": "", "status": "todo",
             "category": "", "priority": "low", "created_at": "2026-01-01T00:00:00",
             "updated_at": "2026-01-01T00:00:00", "deleted_at": None, "expires_at": None},
        ]
        self._write_json(records)
        # FIXED: deleted_at=None is now correctly handled; no workaround needed
        self.ios.import_json(self.json_tmp, self.repo)
        items = self.repo.list()
        self.assertEqual(len(items), 1)
        self.assertNotEqual(items[0].id, 9999)

    def test_import_json_format_error(self):
        """import_json: malformed JSON raises json.JSONDecodeError."""
        with open(self.json_tmp, "w") as f:
            f.write("{not valid json")
        with self.assertRaises(json.JSONDecodeError):
            self.ios.import_json(self.json_tmp, self.repo)

    def test_import_json_non_list_root(self):
        """import_json: root is dict, not list — raises ValueError."""
        self._write_json({"title": "oops"})
        with self.assertRaises(ValueError):
            self.ios.import_json(self.json_tmp, self.repo)

    def test_import_json_round_trip(self):
        """import_json: export then import round-trip preserves all active records."""
        from models import BacklogItem
        import io_service as ios

        db_tmp2 = tempfile.mktemp(suffix=".db")
        from repository import BacklogRepository
        repo2 = BacklogRepository(db_path=db_tmp2)
        try:
            items = [
                BacklogItem(title="Round Trip A", description="desc a"),
                BacklogItem(title="Round Trip B", description="desc b"),
            ]
            export_tmp = tempfile.mktemp(suffix=".json")
            try:
                count = ios.export_json(items, export_tmp)
                self.assertEqual(count, 2)
                imported, skipped = ios.import_json(export_tmp, repo2)
                self.assertEqual(imported, 2, "All exported records should be imported")
                self.assertEqual(skipped, 0, "No active records should be skipped")
                imported_items = repo2.list()
                self.assertEqual(len(imported_items), 2)
                titles = {it.title for it in imported_items}
                self.assertIn("Round Trip A", titles)
                self.assertIn("Round Trip B", titles)
            finally:
                if os.path.exists(export_tmp):
                    os.remove(export_tmp)
        finally:
            repo2.close()
            if os.path.exists(db_tmp2):
                os.remove(db_tmp2)

    def test_import_json_skips_empty_title(self):
        """import_json: record with empty title is skipped."""
        records = [
            {"id": 1, "title": "", "description": "no title", "status": "todo",
             "category": "", "priority": "medium", "created_at": "2026-01-01T00:00:00",
             "updated_at": "2026-01-01T00:00:00", "deleted_at": "", "expires_at": ""},
            {"id": 2, "title": "Valid", "description": "", "status": "todo",
             "category": "", "priority": "medium", "created_at": "2026-01-01T00:00:00",
             "updated_at": "2026-01-01T00:00:00", "deleted_at": "", "expires_at": ""},
        ]
        self._write_json(records)
        imported, skipped = self.ios.import_json(self.json_tmp, self.repo)
        self.assertEqual(imported, 1)
        self.assertEqual(skipped, 1)


class TestImportCsv(unittest.TestCase):
    def setUp(self):
        import io_service as ios
        from repository import BacklogRepository
        from io_service import CSV_FIELDS

        self.ios = ios
        self.BacklogRepository = BacklogRepository
        self.CSV_FIELDS = CSV_FIELDS
        self.db_tmp = tempfile.mktemp(suffix=".db")
        self.repo = BacklogRepository(db_path=self.db_tmp)
        self.csv_tmp = tempfile.mktemp(suffix=".csv")

    def tearDown(self):
        self.repo.close()
        for f in [self.db_tmp, self.csv_tmp]:
            if os.path.exists(f):
                os.remove(f)

    def _write_csv(self, rows):
        with open(self.csv_tmp, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def _make_row(self, title="Task", **kwargs):
        row = {
            "id": "1", "title": title, "description": "", "status": "todo",
            "category": "", "priority": "medium", "created_at": "", "updated_at": "",
            "deleted_at": "", "expires_at": "",
        }
        row.update(kwargs)
        return row

    def test_import_csv_normal(self):
        """import_csv: valid rows, all imported."""
        rows = [self._make_row("Alpha"), self._make_row("Beta")]
        self._write_csv(rows)
        imported, skipped = self.ios.import_csv(self.csv_tmp, self.repo)
        self.assertEqual(imported, 2)
        self.assertEqual(skipped, 0)

    def test_import_csv_skips_empty_title(self):
        """import_csv: row with empty title is skipped."""
        rows = [self._make_row(""), self._make_row("Good")]
        self._write_csv(rows)
        imported, skipped = self.ios.import_csv(self.csv_tmp, self.repo)
        self.assertEqual(imported, 1)
        self.assertEqual(skipped, 1)

    def test_import_csv_id_reassigned(self):
        """import_csv: original id in CSV is ignored; repo assigns new id."""
        rows = [self._make_row("Reassign Me", id="5555")]
        self._write_csv(rows)
        self.ios.import_csv(self.csv_tmp, self.repo)
        items = self.repo.list()
        self.assertEqual(len(items), 1)
        self.assertNotEqual(items[0].id, 5555)


class TestRepositoryListNoLimit(unittest.TestCase):
    def setUp(self):
        from repository import BacklogRepository
        from models import BacklogItem

        self.db_tmp = tempfile.mktemp(suffix=".db")
        self.repo = BacklogRepository(db_path=self.db_tmp)
        self.BacklogItem = BacklogItem

    def tearDown(self):
        self.repo.close()
        if os.path.exists(self.db_tmp):
            os.remove(self.db_tmp)

    def test_list_no_limit_returns_all(self):
        """repo.list() with no limit argument returns all items."""
        for i in range(25):
            self.repo.create(self.BacklogItem(title=f"Item {i}"))
        items = self.repo.list()
        self.assertEqual(len(items), 25)

    def test_list_with_limit_returns_subset(self):
        """repo.list(limit=5) returns exactly 5 items."""
        for i in range(10):
            self.repo.create(self.BacklogItem(title=f"Item {i}"))
        items = self.repo.list(limit=5)
        self.assertEqual(len(items), 5)


class TestAppImports(unittest.TestCase):
    def test_app_module_no_syntax_error(self):
        """app.py parses without syntax errors."""
        app_path = os.path.join(os.path.dirname(__file__), "src", "app.py")
        with open(app_path, encoding="utf-8") as f:
            source = f.read()
        try:
            ast.parse(source)
            parsed = True
        except SyntaxError:
            parsed = False
        self.assertTrue(parsed)

    def test_export_screen_class_exists(self):
        """ExportScreen class exists in app module."""
        import app
        self.assertTrue(hasattr(app, "ExportScreen"))

    def test_import_screen_class_exists(self):
        """ImportScreen class exists in app module."""
        import app
        self.assertTrue(hasattr(app, "ImportScreen"))

    def test_item_form_screen_accepts_categories(self):
        """ItemFormScreen.__init__ accepts a categories parameter."""
        import inspect
        import app
        sig = inspect.signature(app.ItemFormScreen.__init__)
        self.assertIn("categories", sig.parameters)

    def test_backlog_app_has_export_binding(self):
        """BacklogApp has ctrl+e export binding."""
        import app
        bindings = [b.key for b in app.BacklogApp.BINDINGS]
        self.assertIn("ctrl+e", bindings)

    def test_backlog_app_has_import_binding(self):
        """BacklogApp has ctrl+i import binding."""
        import app
        bindings = [b.key for b in app.BacklogApp.BINDINGS]
        self.assertIn("ctrl+i", bindings)


if __name__ == "__main__":
    unittest.main(verbosity=2)
