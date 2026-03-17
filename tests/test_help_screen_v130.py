"""Tests for v1.3.0 help-screen: width 80, Main List Columns order."""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _read_source(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


HELP_SCREEN_PY = os.path.join(os.path.dirname(__file__), "..", "src", "screens", "help_screen.py")
_SOURCE = _read_source(HELP_SCREEN_PY)


class TestHelpContainerWidth(unittest.TestCase):
    """#help-container width must be 80 (v1.3.0 changed from 60)."""

    def test_help_container_width_is_80(self):
        m = re.search(
            r"#help-container\s*\{[^}]*width\s*:\s*(\d+)\s*;",
            _SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "#help-container CSS block not found")
        self.assertEqual(int(m.group(1)), 80)


class TestMainListColumnsOrder(unittest.TestCase):
    """Main List Columns section must have order: ID, Category, Title, Status, Priority, Age."""

    def test_main_list_columns_id_before_category(self):
        """Within Main List Columns, ID must appear before Category."""
        # Extract Main List Columns section (between heading and next [bold] section)
        start = _SOURCE.find("[bold] Main List Columns[/bold]")
        self.assertGreater(start, -1, "Main List Columns heading not found")
        end = _SOURCE.find("[bold]", start + 1)
        if end == -1:
            end = len(_SOURCE)
        section = _SOURCE[start:end]
        idx_id = section.find("ID")
        idx_category = section.find("Category")
        self.assertGreater(idx_id, -1, "ID not found in Main List Columns")
        self.assertGreater(idx_category, -1, "Category not found in Main List Columns")
        self.assertLess(idx_id, idx_category, "ID must appear before Category in Main List Columns")

    def test_main_list_columns_category_before_title(self):
        """Within Main List Columns, Category must appear before Title."""
        start = _SOURCE.find("[bold] Main List Columns[/bold]")
        self.assertGreater(start, -1, "Main List Columns heading not found")
        end = _SOURCE.find("[bold]", start + 1)
        if end == -1:
            end = len(_SOURCE)
        section = _SOURCE[start:end]
        idx_category = section.find("Category")
        idx_title = section.find("Title")
        self.assertGreater(idx_category, -1, "Category not found in Main List Columns")
        self.assertGreater(idx_title, -1, "Title not found in Main List Columns")
        self.assertLess(idx_category, idx_title, "Category must appear before Title in Main List Columns")


if __name__ == "__main__":
    unittest.main()
