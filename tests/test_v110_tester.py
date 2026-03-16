"""Tester Agent: additional boundary & edge-case tests for v1.1.0 features."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


# ---------------------------------------------------------------------------
# 1. ConfirmQuitScreen — compose() widget structure
# ---------------------------------------------------------------------------

def _get_confirm_quit_source() -> str:
    path = os.path.join(PROJECT_ROOT, "src", "screens", "confirm_quit.py")
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestConfirmQuitScreenCompose(unittest.TestCase):
    """Verify compose() widget structure via source inspection (avoids Textual app context)."""

    def setUp(self):
        self.source = _get_confirm_quit_source()

    def test_compose_yields_vertical_container(self):
        self.assertIn('Vertical(id="quit-confirm-container")', self.source)

    def test_compose_yields_quit_label(self):
        self.assertIn("Quit Backlog Manager", self.source)

    def test_compose_yields_horizontal_buttons(self):
        self.assertIn('Horizontal(id="quit-confirm-buttons")', self.source)

    def test_compose_yields_yn_instructions(self):
        self.assertIn("Y/Enter", self.source)
        self.assertIn("N/Esc", self.source)

    def test_css_contains_container_id(self):
        from screens.confirm_quit import ConfirmQuitScreen
        self.assertIn("quit-confirm-container", ConfirmQuitScreen.CSS)

    def test_css_contains_buttons_id(self):
        from screens.confirm_quit import ConfirmQuitScreen
        self.assertIn("quit-confirm-buttons", ConfirmQuitScreen.CSS)

    def test_css_centers_dialog(self):
        from screens.confirm_quit import ConfirmQuitScreen
        self.assertIn("align: center middle", ConfirmQuitScreen.CSS)


class TestConfirmQuitBindingDetails(unittest.TestCase):
    """Verify specific binding properties beyond key existence."""

    def test_enter_binding_is_hidden(self):
        """'enter' binding should have show=False to avoid cluttering footer."""
        from screens.confirm_quit import ConfirmQuitScreen
        enter_bindings = [b for b in ConfirmQuitScreen.BINDINGS if b.key == "enter"]
        self.assertEqual(len(enter_bindings), 1)
        self.assertFalse(enter_bindings[0].show, "enter binding should be hidden (show=False)")

    def test_y_binding_action_is_confirm(self):
        from screens.confirm_quit import ConfirmQuitScreen
        y_bindings = [b for b in ConfirmQuitScreen.BINDINGS if b.key == "y"]
        self.assertEqual(y_bindings[0].action, "confirm")

    def test_n_binding_action_is_cancel(self):
        from screens.confirm_quit import ConfirmQuitScreen
        n_bindings = [b for b in ConfirmQuitScreen.BINDINGS if b.key == "n"]
        self.assertEqual(n_bindings[0].action, "cancel")

    def test_escape_binding_action_is_cancel(self):
        from screens.confirm_quit import ConfirmQuitScreen
        esc_bindings = [b for b in ConfirmQuitScreen.BINDINGS if b.key == "escape"]
        self.assertEqual(esc_bindings[0].action, "cancel")

    def test_exactly_four_bindings(self):
        from screens.confirm_quit import ConfirmQuitScreen
        self.assertEqual(len(ConfirmQuitScreen.BINDINGS), 4)


# ---------------------------------------------------------------------------
# 2. pyproject.toml — build-backend correctness & version
# ---------------------------------------------------------------------------

class TestPyprojectBuildBackend(unittest.TestCase):
    """build-backend must be setuptools.build_meta, NOT legacy."""

    def setUp(self):
        path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        with open(path, encoding="utf-8") as f:
            self.content = f.read()

    def test_not_legacy_backend(self):
        self.assertNotIn("_legacy", self.content,
                         "build-backend must not reference legacy setuptools backend")
        self.assertNotIn("_Backend", self.content)

    def test_build_backend_exact_value(self):
        self.assertIn('build-backend = "setuptools.build_meta"', self.content)

    def test_pyproject_version_is_110(self):
        """pyproject.toml itself must declare version = '1.1.0'."""
        self.assertIn('version = "1.1.0"', self.content)

    def test_requires_setuptools_ge_64(self):
        self.assertIn("setuptools>=64", self.content)


# ---------------------------------------------------------------------------
# 3. HelpScreen — q key description consistency (CR P2 fix verification)
# ---------------------------------------------------------------------------

class TestHelpScreenQuitDescription(unittest.TestCase):
    """Help screen must show 'Quit (with confirmation)' for q key."""

    def setUp(self):
        path = os.path.join(PROJECT_ROOT, "src", "screens", "help_screen.py")
        with open(path, encoding="utf-8") as f:
            self.source = f.read()

    def test_q_description_has_confirmation(self):
        self.assertIn("Quit (with confirmation)", self.source)

    def test_no_bare_quit_for_q_key(self):
        """Should not have a line with just 'q ... Quit' without confirmation note."""
        for line in self.source.splitlines():
            if "q " in line and "Quit" in line and "Label" in line:
                self.assertIn("confirmation", line,
                              f"q-key line should mention confirmation: {line.strip()}")

    def test_config_path_no_fstring(self):
        """Config file path line should NOT use f-string (CR P2 fix)."""
        for line in self.source.splitlines():
            if "~/.backlog/config.json" in line and "Label" in line:
                stripped = line.strip()
                self.assertFalse(
                    stripped.startswith("yield Label(f"),
                    f"Config path line should not use f-string: {stripped}")


# ---------------------------------------------------------------------------
# 4. action_request_quit — source-level reference check
# ---------------------------------------------------------------------------

class TestActionRequestQuitReferencesConfirmQuitScreen(unittest.TestCase):
    """action_request_quit must use ConfirmQuitScreen (not raw quit)."""

    def setUp(self):
        path = os.path.join(PROJECT_ROOT, "src", "app.py")
        with open(path, encoding="utf-8") as f:
            self.source = f.read()

    def test_action_references_confirm_quit_screen(self):
        self.assertIn("ConfirmQuitScreen()", self.source)

    def test_action_does_not_call_self_quit_directly(self):
        """action_request_quit should not call self.quit() directly."""
        in_method = False
        for line in self.source.splitlines():
            if "def action_request_quit" in line:
                in_method = True
                continue
            if in_method:
                if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    break
                if "def " in line and "action_request_quit" not in line:
                    break
                self.assertNotIn("self.quit()", line,
                                 "action_request_quit must not call self.quit() directly")


# ---------------------------------------------------------------------------
# 5. Version consistency across ALL locations
# ---------------------------------------------------------------------------

class TestAllVersionsConsistent(unittest.TestCase):
    """All version declarations must be exactly '1.1.0'."""

    def test_pyproject_toml(self):
        path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn('version = "1.1.0"', content)

    def test_src_init(self):
        from __init__ import __version__
        self.assertEqual(__version__, "1.1.0")

    def test_readme_badge(self):
        path = os.path.join(PROJECT_ROOT, "README.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("1.1.0", content)

    def test_readme_version_check_example(self):
        """README 'Check version' example output must say 1.1.0 (P1 fix)."""
        path = os.path.join(PROJECT_ROOT, "README.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("# backlog 1.1.0", content)
        self.assertNotIn("# backlog 1.0.0", content,
                         "README should not have outdated version example")


if __name__ == "__main__":
    unittest.main()
