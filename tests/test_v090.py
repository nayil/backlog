"""Tests for v0.9.0: colors module and screens imports."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rich.text import Text

from models import Status, Priority
from colors import (
    STATUS_DISPLAY,
    PRIORITY_DISPLAY,
    NEXT_STATUS,
    colorize_status,
    colorize_priority,
)
from color_config import ColorConfig


# ── colors.py tests ─────────────────────────────────────────────────────────


class TestStatusDisplayMapping(unittest.TestCase):
    def test_status_display_mapping(self):
        for s in Status:
            self.assertIn(s, STATUS_DISPLAY, f"{s} missing from STATUS_DISPLAY")


class TestPriorityDisplayMapping(unittest.TestCase):
    def test_priority_display_mapping(self):
        for p in Priority:
            self.assertIn(p, PRIORITY_DISPLAY, f"{p} missing from PRIORITY_DISPLAY")


class TestNextStatusMapping(unittest.TestCase):
    def test_next_status_mapping(self):
        self.assertEqual(NEXT_STATUS[Status.TODO], Status.IN_PROGRESS)
        self.assertEqual(NEXT_STATUS[Status.IN_PROGRESS], Status.DONE)
        self.assertEqual(NEXT_STATUS[Status.DONE], Status.IN_PROGRESS)


class TestColorizeStatusWithConfig(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.cc = ColorConfig(config_path=self.config_file)

    def test_returns_text(self):
        result = colorize_status(Status.TODO, self.cc)
        self.assertIsInstance(result, Text)

    def test_uses_default_color(self):
        result = colorize_status(Status.TODO, self.cc)
        style_str = str(result.style) if result.style else ""
        self.assertIn("#61afef", style_str.lower())

    def test_uses_custom_color(self):
        import json
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"todo": "#FF0000"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        result = colorize_status(Status.TODO, cc)
        style_str = str(result.style) if result.style else ""
        self.assertIn("#ff0000", style_str.lower())


class TestColorizePriorityWithConfig(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.cc = ColorConfig(config_path=self.config_file)

    def test_returns_text(self):
        result = colorize_priority(Priority.HIGH, self.cc)
        self.assertIsInstance(result, Text)

    def test_uses_default_color(self):
        result = colorize_priority(Priority.HIGH, self.cc)
        style_str = str(result.style) if result.style else ""
        self.assertIn("#e06c75", style_str.lower())


# ── screens/ import tests ───────────────────────────────────────────────────


class TestScreensImport(unittest.TestCase):
    def test_import_all_screens(self):
        from screens import (
            ItemFormScreen,
            SearchScreen,
            ConfirmDeleteScreen,
            TrashScreen,
            HelpScreen,
            VersionScreen,
            ExportScreen,
            ImportScreen,
        )
        classes = [
            ItemFormScreen, SearchScreen, ConfirmDeleteScreen,
            TrashScreen, HelpScreen, VersionScreen,
            ExportScreen, ImportScreen,
        ]
        self.assertEqual(len(classes), 8)

    def test_screen_classes_are_modal(self):
        from textual.screen import ModalScreen
        from screens import (
            ItemFormScreen, SearchScreen, ConfirmDeleteScreen,
            TrashScreen, HelpScreen, VersionScreen,
            ExportScreen, ImportScreen,
        )
        for cls in [
            ItemFormScreen, SearchScreen, ConfirmDeleteScreen,
            TrashScreen, HelpScreen, VersionScreen,
            ExportScreen, ImportScreen,
        ]:
            self.assertTrue(
                issubclass(cls, ModalScreen),
                f"{cls.__name__} is not a subclass of ModalScreen",
            )


# ── app.py line count test ──────────────────────────────────────────────────


class TestAppLineCount(unittest.TestCase):
    def test_app_line_count(self):
        app_path = os.path.join(os.path.dirname(__file__), "..", "src", "app.py")
        with open(app_path) as f:
            line_count = sum(1 for _ in f)
        self.assertLessEqual(line_count, 500, f"app.py has {line_count} lines, exceeds 500")


if __name__ == "__main__":
    unittest.main()
