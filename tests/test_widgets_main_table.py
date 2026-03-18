"""Tests for widgets.main_table module — MainTable component."""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import BacklogItem, Status


class TestMainTableSelectedItemIdEmpty(unittest.TestCase):
    """Empty table: selected_item_id is None."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.db_path = os.path.join(self.tmpdir, "backlog.db")
        with open(self.config_file, "w") as f:
            json.dump({}, f)

    def test_main_table_selected_item_id_empty(self):
        """When table has no rows, selected_item_id returns None."""
        from config import BacklogConfig
        from repository import BacklogRepository
        from color_config import ColorConfig
        from textual.app import App
        from textual.widgets import DataTable, Static
        from widgets.main_table import MainTable

        config_file = self.config_file
        db_path = self.db_path

        class TestApp(App):
            def __init__(self, config_file, db_path):
                super().__init__()
                self._config_file = config_file
                self._db_path = db_path

            def compose(self):
                self._preview_title = Static("", id="preview-title")
                self._preview_desc = Static("", id="preview-desc")
                config = BacklogConfig(config_path=self._config_file)
                color_config = ColorConfig()
                repo = BacklogRepository(self._db_path)
                table = MainTable(
                    repo=repo,
                    config=config,
                    color_config=color_config,
                    preview_title=self._preview_title,
                    preview_desc=self._preview_desc,
                    on_sort_changed=None,
                    id="table",
                )
                yield table
                yield self._preview_title
                yield self._preview_desc

        app = TestApp(config_file=config_file, db_path=db_path)

        async def run():
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause(0.2)
                table = app.query_one("#table", MainTable)
                table.refresh(
                    filter_status=None,
                    filter_category=None,
                    filter_keyword=None,
                    page=0,
                    page_size=20,
                    sort_by=None,
                    sort_asc=True,
                )
                await pilot.pause(0.1)
                self.assertIsNone(table.selected_item_id)

        asyncio.run(run())


class TestMainTableRefreshLoadsRows(unittest.TestCase):
    """refresh() loads rows from repo."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.db_path = os.path.join(self.tmpdir, "backlog.db")
        with open(self.config_file, "w") as f:
            json.dump({}, f)

    def test_main_table_refresh_loads_rows(self):
        """When repo has 2 items, refresh displays 2 rows."""
        from config import BacklogConfig
        from repository import BacklogRepository
        from color_config import ColorConfig
        from textual.app import App
        from textual.widgets import Static
        from widgets.main_table import MainTable

        config_file = self.config_file
        db_path = self.db_path

        repo = BacklogRepository(db_path)
        repo.create(BacklogItem(title="Item A"))
        repo.create(BacklogItem(title="Item B"))
        repo.close()

        class TestApp(App):
            def __init__(self, config_file, db_path):
                super().__init__()
                self._config_file = config_file
                self._db_path = db_path

            def compose(self):
                self._preview_title = Static("", id="preview-title")
                self._preview_desc = Static("", id="preview-desc")
                config = BacklogConfig(config_path=self._config_file)
                color_config = ColorConfig()
                r = BacklogRepository(self._db_path)
                table = MainTable(
                    repo=r,
                    config=config,
                    color_config=color_config,
                    preview_title=self._preview_title,
                    preview_desc=self._preview_desc,
                    on_sort_changed=None,
                    id="table",
                )
                yield table
                yield self._preview_title
                yield self._preview_desc

        app = TestApp(config_file=config_file, db_path=db_path)

        async def run():
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause(0.2)
                table = app.query_one("#table", MainTable)
                table.refresh(
                    filter_status=None,
                    filter_category=None,
                    filter_keyword=None,
                    page=0,
                    page_size=20,
                    sort_by=None,
                    sort_asc=True,
                )
                await pilot.pause(0.1)
                self.assertEqual(table.row_count, 2)

        asyncio.run(run())


class TestMainTableHasColumns(unittest.TestCase):
    """MainTable has expected columns after on_mount."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.db_path = os.path.join(self.tmpdir, "backlog.db")
        with open(self.config_file, "w") as f:
            json.dump({}, f)

    def test_main_table_has_columns(self):
        """After mount, columns are ID, Category, Title, Status, Priority, Age."""
        from config import BacklogConfig
        from repository import BacklogRepository
        from color_config import ColorConfig
        from textual.app import App
        from textual.widgets import Static
        from widgets.main_table import MainTable

        config_file = self.config_file
        db_path = self.db_path

        class TestApp(App):
            def __init__(self, config_file, db_path):
                super().__init__()
                self._config_file = config_file
                self._db_path = db_path

            def compose(self):
                self._preview_title = Static("", id="preview-title")
                self._preview_desc = Static("", id="preview-desc")
                config = BacklogConfig(config_path=self._config_file)
                color_config = ColorConfig()
                repo = BacklogRepository(self._db_path)
                table = MainTable(
                    repo=repo,
                    config=config,
                    color_config=color_config,
                    preview_title=self._preview_title,
                    preview_desc=self._preview_desc,
                    on_sort_changed=None,
                    id="table",
                )
                yield table
                yield self._preview_title
                yield self._preview_desc

        app = TestApp(config_file=config_file, db_path=db_path)

        async def run():
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause(0.2)
                table = app.query_one("#table", MainTable)
                col_labels = [str(c.label) for c in table.columns.values()]
                self.assertIn("ID", col_labels)
                self.assertIn("Category", col_labels)
                self.assertIn("Title", col_labels)
                self.assertIn("Status", col_labels)
                self.assertIn("Priority", col_labels)
                self.assertIn("Age", col_labels)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
