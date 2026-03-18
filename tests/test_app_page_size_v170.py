"""Tests for v1.7.0: page_size from config, page clamp, status bar content."""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import BacklogItem, Status


class TestAppPageSizeFromConfig(unittest.TestCase):
    """App uses page_size from config.get_page_size()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.db_path = os.path.join(self.tmpdir, "backlog.db")

    def test_page_size_from_config_default(self):
        """When config has no page_size, app uses default 20."""
        with open(self.config_file, "w") as f:
            json.dump({}, f)
        with patch("app.BacklogConfig") as MockConfig:
            from config import BacklogConfig
            real_config = BacklogConfig(config_path=self.config_file)
            MockConfig.return_value = real_config
            from app import BacklogApp
            app = BacklogApp(db_path=self.db_path)
            self.assertEqual(app.page_size, 20)

    def test_page_size_from_config_custom(self):
        """When config has page_size=5, app uses 5."""
        with open(self.config_file, "w") as f:
            json.dump({"page_size": 5}, f)
        with patch("app.BacklogConfig") as MockConfig:
            from config import BacklogConfig
            real_config = BacklogConfig(config_path=self.config_file)
            MockConfig.return_value = real_config
            from app import BacklogApp
            app = BacklogApp(db_path=self.db_path)
            self.assertEqual(app.page_size, 5)


class TestAppPageClamp(unittest.TestCase):
    """Page clamp when total_pages decreases (filter change, etc)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.db_path = os.path.join(self.tmpdir, "backlog.db")

    def _create_items(self, repo, count: int, status: Status = Status.TODO):
        for i in range(count):
            repo.create(BacklogItem(title=f"Item {i}", status=status))

    def test_page_clamp_when_filter_reduces_pages(self):
        """When on page 2 and filter reduces to 1 page, page clamps to 0."""
        with open(self.config_file, "w") as f:
            json.dump({"page_size": 10}, f)

        with patch("app.BacklogConfig") as MockConfig:
            from config import BacklogConfig
            from repository import BacklogRepository
            from app import BacklogApp

            real_config = BacklogConfig(config_path=self.config_file)
            MockConfig.return_value = real_config

            repo = BacklogRepository(self.db_path)
            self._create_items(repo, 5, Status.TODO)
            self._create_items(repo, 20, Status.DONE)
            repo.close()

            app = BacklogApp(db_path=self.db_path)

            async def run():
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause(0.3)
                    app.filter_status = Status.TODO
                    app.page = 2
                    app._refresh_table()
                    self.assertEqual(app.page, 0, "page should clamp to 0 when filter yields 5 items on 1 page")

            asyncio.run(run())

    def test_page_clamp_total_count_zero(self):
        """When total_count=0, total_pages=1, page stays 0."""
        with open(self.config_file, "w") as f:
            json.dump({"page_size": 10}, f)

        with patch("app.BacklogConfig") as MockConfig:
            from config import BacklogConfig
            from app import BacklogApp

            real_config = BacklogConfig(config_path=self.config_file)
            MockConfig.return_value = real_config

            app = BacklogApp(db_path=self.db_path)

            async def run():
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause(0.3)
                    self.assertEqual(app.page, 0)
                    self.assertEqual(app._total_count, 0)

            asyncio.run(run())


class TestAppStatusBarContent(unittest.TestCase):
    """Status bar (stats-bar) displays Total, Todo, In Progress, Done, Page X/Y."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.db_path = os.path.join(self.tmpdir, "backlog.db")

    def test_status_bar_has_total_and_page(self):
        """Stats bar contains Total and Page X/Y."""
        with open(self.config_file, "w") as f:
            json.dump({"page_size": 5}, f)

        with patch("app.BacklogConfig") as MockConfig:
            from config import BacklogConfig
            from repository import BacklogRepository
            from app import BacklogApp

            real_config = BacklogConfig(config_path=self.config_file)
            MockConfig.return_value = real_config

            repo = BacklogRepository(self.db_path)
            repo.create(BacklogItem(title="A", status=Status.TODO))
            repo.create(BacklogItem(title="B", status=Status.IN_PROGRESS))
            repo.close()

            app = BacklogApp(db_path=self.db_path)

            async def run():
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause(0.3)
                    bar = app.query_one("#stats-bar")
                    text = getattr(bar, "content", None) or getattr(bar, "renderable", None)
                    if text is not None:
                        text = str(text)
                    else:
                        text = str(bar)
                    self.assertIn("Total:", text)
                    self.assertIn("Page", text)
                    self.assertIn("1/", text)
                    self.assertIn("Todo:", text)
                    self.assertIn("In Progress:", text)
                    self.assertIn("Done:", text)

            asyncio.run(run())


class TestAppPageSizePagination(unittest.TestCase):
    """Pagination respects page_size from config."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.db_path = os.path.join(self.tmpdir, "backlog.db")

    def test_table_shows_page_size_rows(self):
        """With page_size=3 and 10 items, first page shows 3 rows."""
        with open(self.config_file, "w") as f:
            json.dump({"page_size": 3}, f)

        with patch("app.BacklogConfig") as MockConfig:
            from config import BacklogConfig
            from repository import BacklogRepository
            from app import BacklogApp

            real_config = BacklogConfig(config_path=self.config_file)
            MockConfig.return_value = real_config

            repo = BacklogRepository(self.db_path)
            for i in range(10):
                repo.create(BacklogItem(title=f"Item {i}"))
            repo.close()

            app = BacklogApp(db_path=self.db_path)

            async def run():
                async with app.run_test(size=(120, 40)) as pilot:
                    await pilot.pause(0.3)
                    table = app.query_one("#table")
                    self.assertEqual(table.row_count, 3, "page_size=3 should show 3 rows on first page")

            asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
