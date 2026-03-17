"""Tests for ItemFormScreen._has_changes and action_cancel flow."""

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from textual.app import App
from models import BacklogItem, Priority, Status
from screens.confirm_discard import ConfirmDiscardScreen


# Minimal test app that pushes ItemFormScreen for _has_changes testing
class ItemFormTestApp(App):
    """App that mounts ItemFormScreen for testing."""

    def __init__(self, item=None, categories=None):
        super().__init__()
        self._form_item = item
        self._form_categories = categories or []
        self.form_screen = None

    def on_mount(self):
        from screens.item_form import ItemFormScreen
        self.form_screen = ItemFormScreen(item=self._form_item, categories=self._form_categories)
        self.push_screen(self.form_screen)


# ---------------------------------------------------------------------------
# _has_changes - New mode
# ---------------------------------------------------------------------------

class TestHasChangesNewMode(unittest.TestCase):
    """New mode: any non-empty or priority != MEDIUM -> True."""

    def test_new_mode_all_empty_priority_medium_false(self):
        async def run():
            app = ItemFormTestApp(item=None, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                return app.form_screen._has_changes()
        self.assertFalse(asyncio.run(run()))

    def test_new_mode_title_non_empty_true(self):
        async def run():
            app = ItemFormTestApp(item=None, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-title").value = "foo"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))

    def test_new_mode_description_non_empty_true(self):
        async def run():
            app = ItemFormTestApp(item=None, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-desc").text = "bar"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))

    def test_new_mode_category_non_empty_true(self):
        async def run():
            app = ItemFormTestApp(item=None, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-category").value = "cat"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))

    def test_new_mode_priority_not_medium_true(self):
        async def run():
            app = ItemFormTestApp(item=None, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#sel-priority").value = "high"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))


# ---------------------------------------------------------------------------
# _has_changes - Edit mode
# ---------------------------------------------------------------------------

class TestHasChangesEditMode(unittest.TestCase):
    """Edit mode: any field different from initial item -> True."""

    def test_edit_mode_identical_false(self):
        item = BacklogItem(
            title="t",
            description="d",
            category="c",
            priority=Priority.HIGH,
            status=Status.TODO,
        )

        async def run():
            app = ItemFormTestApp(item=item, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                return app.form_screen._has_changes()
        self.assertFalse(asyncio.run(run()))

    def test_edit_mode_title_different_true(self):
        item = BacklogItem(title="orig", description="", category="", priority=Priority.MEDIUM)

        async def run():
            app = ItemFormTestApp(item=item, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-title").value = "changed"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))

    def test_edit_mode_description_different_true(self):
        item = BacklogItem(title="t", description="orig", category="", priority=Priority.MEDIUM)

        async def run():
            app = ItemFormTestApp(item=item, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-desc").text = "changed"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))

    def test_edit_mode_category_different_true(self):
        item = BacklogItem(title="t", description="", category="orig", priority=Priority.MEDIUM)

        async def run():
            app = ItemFormTestApp(item=item, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-category").value = "changed"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))

    def test_edit_mode_priority_different_true(self):
        item = BacklogItem(title="t", description="", category="", priority=Priority.LOW)

        async def run():
            app = ItemFormTestApp(item=item, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#sel-priority").value = "high"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))

    def test_edit_mode_status_different_true(self):
        item = BacklogItem(title="t", description="", category="", priority=Priority.MEDIUM, status=Status.TODO)

        async def run():
            app = ItemFormTestApp(item=item, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#sel-status").value = "in_progress"
                return app.form_screen._has_changes()
        self.assertTrue(asyncio.run(run()))


# ---------------------------------------------------------------------------
# action_cancel - ConfirmDiscardScreen integration
# ---------------------------------------------------------------------------

class TestActionCancelImportsConfirmDiscard(unittest.TestCase):
    """ItemFormScreen.action_cancel uses ConfirmDiscardScreen when has changes."""

    def test_item_form_imports_confirm_discard(self):
        path = os.path.join(os.path.dirname(__file__), "..", "src", "screens", "item_form.py")
        with open(path, encoding="utf-8") as f:
            source = f.read()
        self.assertIn("ConfirmDiscardScreen", source)
        self.assertIn("from screens.confirm_discard import ConfirmDiscardScreen", source)

    def test_action_cancel_checks_has_changes(self):
        path = os.path.join(os.path.dirname(__file__), "..", "src", "screens", "item_form.py")
        with open(path, encoding="utf-8") as f:
            source = f.read()
        self.assertIn("_has_changes()", source)
        self.assertIn("push_screen(ConfirmDiscardScreen()", source)
        self.assertIn("on_discard_result", source)

    def test_action_cancel_with_changes_esc_shows_confirm_discard(self):
        """With unsaved changes, Esc shows ConfirmDiscardScreen."""
        async def run():
            app = ItemFormTestApp(item=None, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-title").value = "foo"
                await pilot.press("escape")
                await pilot.pause(0.2)
                return any(isinstance(s, ConfirmDiscardScreen) for s in app.screen_stack)
        self.assertTrue(asyncio.run(run()))

    def test_action_cancel_confirm_y_dismisses_form(self):
        """With changes, Esc then Y dismisses ItemFormScreen."""
        async def run():
            app = ItemFormTestApp(item=None, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-title").value = "foo"
                await pilot.press("escape")
                await pilot.pause(0.2)
                await pilot.press("y")
                await pilot.pause(0.2)
                return app.form_screen not in app.screen_stack
        self.assertTrue(asyncio.run(run()))

    def test_action_cancel_confirm_n_keeps_form_open(self):
        """With changes, Esc then N closes confirm screen, form stays open."""
        async def run():
            app = ItemFormTestApp(item=None, categories=[])
            async with app.run_test() as pilot:
                await pilot.pause()
                app.form_screen.query_one("#inp-title").value = "foo"
                await pilot.press("escape")
                await pilot.pause(0.2)
                await pilot.press("n")
                await pilot.pause(0.2)
                confirm_gone = not any(isinstance(s, ConfirmDiscardScreen) for s in app.screen_stack)
                form_still_open = app.form_screen in app.screen_stack
                return confirm_gone and form_still_open
        self.assertTrue(asyncio.run(run()))


if __name__ == "__main__":
    unittest.main()
