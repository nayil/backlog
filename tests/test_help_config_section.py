"""Tests for HelpScreen Configuration section."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _get_help_source() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "src", "screens", "help_screen.py")
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestHelpScreenConfigSection(unittest.TestCase):
    """HelpScreen source must contain Configuration section content."""

    def setUp(self):
        self.source = _get_help_source()

    def test_contains_configuration_heading(self):
        self.assertIn("Configuration", self.source)

    def test_contains_config_path(self):
        self.assertIn("~/.backlog/config.json", self.source)

    def test_contains_status_colors_key(self):
        self.assertIn("status_colors", self.source)

    def test_contains_priority_colors_key(self):
        self.assertIn("priority_colors", self.source)

    def test_references_default_status_colors(self):
        self.assertIn("ColorConfig.DEFAULT_STATUS_COLORS", self.source)

    def test_references_default_priority_colors(self):
        self.assertIn("ColorConfig.DEFAULT_PRIORITY_COLORS", self.source)


class TestColorConfigDefaults(unittest.TestCase):
    """ColorConfig constants contain expected default hex values."""

    def test_default_todo_color(self):
        from color_config import ColorConfig
        self.assertEqual(ColorConfig.DEFAULT_STATUS_COLORS["todo"], "#61AFEF")

    def test_default_in_progress_color(self):
        from color_config import ColorConfig
        self.assertEqual(ColorConfig.DEFAULT_STATUS_COLORS["in_progress"], "#E5C07B")

    def test_default_done_color(self):
        from color_config import ColorConfig
        self.assertEqual(ColorConfig.DEFAULT_STATUS_COLORS["done"], "#98C379")

    def test_default_high_color(self):
        from color_config import ColorConfig
        self.assertEqual(ColorConfig.DEFAULT_PRIORITY_COLORS["high"], "#E06C75")


class TestHelpScreenImportsColorConfig(unittest.TestCase):
    """HelpScreen should reference ColorConfig defaults (not hardcode)."""

    def test_imports_color_config(self):
        self.assertIn("ColorConfig", _get_help_source())


if __name__ == "__main__":
    unittest.main()
