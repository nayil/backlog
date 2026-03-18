"""Tests for widgets.filter_bar module."""

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from textual.app import App, ComposeResult
from textual.widgets import Select

from models import Status


class FilterBarApp(App):
    """Minimal app to mount FilterBar for testing."""

    def __init__(self, categories, filter_status=None, filter_category=None):
        super().__init__()
        self._categories = categories
        self._filter_status = filter_status
        self._filter_category = filter_category

    def compose(self) -> ComposeResult:
        from widgets.filter_bar import FilterBar
        yield FilterBar(
            categories=self._categories,
            filter_status=self._filter_status,
            filter_category=self._filter_category,
        )


class TestFilterBar(unittest.TestCase):
    """FilterBar composes two Selects and supports set_categories."""

    def test_filter_bar_composes_two_selects(self):
        """FilterBar yields #sel-filter-status and #sel-filter-category."""
        app = FilterBarApp(categories=["A", "B"])

        async def run():
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause(0.1)
                status_sel = app.query_one("#sel-filter-status", Select)
                cat_sel = app.query_one("#sel-filter-category", Select)
                self.assertIsNotNone(status_sel)
                self.assertIsNotNone(cat_sel)

        asyncio.run(run())

    def test_filter_bar_category_options(self):
        """Category Select contains All Categories and A, B."""
        app = FilterBarApp(categories=["A", "B"])

        async def run():
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause(0.1)
                cat_sel = app.query_one("#sel-filter-category", Select)
                self.assertIsNotNone(cat_sel)
                # Options are (display, value) tuples
                options = getattr(cat_sel, "_options", None) or getattr(
                    cat_sel, "options", None
                )
                if options is not None:
                    values = [opt[1] for opt in options]
                    self.assertIn("all", values)
                    self.assertIn("A", values)
                    self.assertIn("B", values)
                # Fallback: verify value and widget works
                self.assertEqual(cat_sel.value, "all")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
