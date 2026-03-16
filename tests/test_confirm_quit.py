"""Tests for ConfirmQuitScreen: quit confirmation dialog."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestConfirmQuitScreenExists(unittest.TestCase):
    """ConfirmQuitScreen can be imported from screens package."""

    def test_import(self):
        from screens.confirm_quit import ConfirmQuitScreen
        self.assertTrue(issubclass(ConfirmQuitScreen, object))


class TestConfirmQuitScreenIsModal(unittest.TestCase):
    """ConfirmQuitScreen is a ModalScreen[bool]."""

    def test_is_modal_screen(self):
        from textual.screen import ModalScreen
        from screens.confirm_quit import ConfirmQuitScreen
        self.assertTrue(issubclass(ConfirmQuitScreen, ModalScreen))


class TestConfirmQuitScreenBindings(unittest.TestCase):
    """ConfirmQuitScreen has Y/Enter for confirm and N/Esc for cancel."""

    def test_has_confirm_bindings(self):
        from screens.confirm_quit import ConfirmQuitScreen
        binding_keys = [b.key for b in ConfirmQuitScreen.BINDINGS]
        self.assertIn("y", binding_keys)
        self.assertIn("enter", binding_keys)

    def test_has_cancel_bindings(self):
        from screens.confirm_quit import ConfirmQuitScreen
        binding_keys = [b.key for b in ConfirmQuitScreen.BINDINGS]
        self.assertIn("n", binding_keys)
        self.assertIn("escape", binding_keys)


class TestConfirmQuitScreenActions(unittest.TestCase):
    """ConfirmQuitScreen has action_confirm and action_cancel methods."""

    def test_has_action_confirm(self):
        from screens.confirm_quit import ConfirmQuitScreen
        self.assertTrue(hasattr(ConfirmQuitScreen, "action_confirm"))

    def test_has_action_cancel(self):
        from screens.confirm_quit import ConfirmQuitScreen
        self.assertTrue(hasattr(ConfirmQuitScreen, "action_cancel"))


class TestAppQuitBinding(unittest.TestCase):
    """App.BINDINGS should bind q to action_request_quit (not action_quit)."""

    def test_q_binds_to_request_quit(self):
        from app import BacklogApp
        q_bindings = [b for b in BacklogApp.BINDINGS if b.key == "q"]
        self.assertEqual(len(q_bindings), 1)
        self.assertEqual(q_bindings[0].action, "request_quit")


class TestAppHasRequestQuitAction(unittest.TestCase):
    """BacklogApp must define action_request_quit method."""

    def test_has_action_request_quit(self):
        from app import BacklogApp
        self.assertTrue(hasattr(BacklogApp, "action_request_quit"))


class TestConfirmQuitScreenExportedFromScreens(unittest.TestCase):
    """ConfirmQuitScreen is accessible via screens package."""

    def test_import_from_screens(self):
        from screens import ConfirmQuitScreen
        self.assertIsNotNone(ConfirmQuitScreen)


if __name__ == "__main__":
    unittest.main()
