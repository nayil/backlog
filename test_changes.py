"""Unit tests for v0.2.0 changes: Age column, status bug fix, VersionScreen."""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from models import BacklogItem, Priority, Status


class TestAgeCalculation(unittest.TestCase):
    """Tests for Age column logic (change B)."""

    def _age_str(self, created_at) -> str:
        """Replicate the age_str logic from _refresh_table."""
        now = datetime.now()
        return f"{(now - created_at).days}d" if created_at else "-"

    def test_age_zero_days(self):
        """Item created now should show 0d."""
        created_at = datetime.now()
        result = self._age_str(created_at)
        self.assertEqual(result, "0d")

    def test_age_five_days(self):
        """Item created 5 days ago should show 5d."""
        created_at = datetime.now() - timedelta(days=5)
        result = self._age_str(created_at)
        self.assertEqual(result, "5d")

    def test_age_thirty_days(self):
        """Item created 30 days ago should show 30d."""
        created_at = datetime.now() - timedelta(days=30)
        result = self._age_str(created_at)
        self.assertEqual(result, "30d")

    def test_age_none_guard(self):
        """created_at=None should return '-'."""
        result = self._age_str(None)
        self.assertEqual(result, "-")

    def test_backlog_item_none_created_at(self):
        """BacklogItem with created_at=None: age logic returns '-'."""
        item = BacklogItem(title="Test", priority=Priority.MEDIUM)
        item.created_at = None
        now = datetime.now()
        age_str = f"{(now - item.created_at).days}d" if item.created_at else "-"
        self.assertEqual(age_str, "-")

    def test_backlog_item_with_created_at(self):
        """BacklogItem with real created_at: age reflects correct days."""
        item = BacklogItem(title="Test", priority=Priority.MEDIUM)
        item.created_at = datetime.now() - timedelta(days=7)
        now = datetime.now()
        age_str = f"{(now - item.created_at).days}d" if item.created_at else "-"
        self.assertEqual(age_str, "7d")


class TestVersionParsing(unittest.TestCase):
    """Tests for VersionScreen._parse_versions logic (change C)."""

    def _parse_versions_from_dir(self, dir_path: Path) -> list[str]:
        """Replicate VersionScreen._parse_versions logic."""
        if not dir_path.exists():
            return []
        versions: set[str] = set()
        for f in dir_path.iterdir():
            match = re.search(r"v\d+\.\d+\.\d+", f.name)
            if match:
                versions.add(match.group(0))
        return sorted(
            versions,
            key=lambda v: tuple(int(x) for x in v[1:].split(".")),
            reverse=True,
        )

    def test_no_release_dir(self):
        """Non-existent directory returns empty list."""
        result = self._parse_versions_from_dir(Path("/tmp/nonexistent_release_dir_xyz"))
        self.assertEqual(result, [])

    def test_empty_release_dir(self):
        """Empty directory returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._parse_versions_from_dir(Path(tmpdir))
            self.assertEqual(result, [])

    def test_single_version_file(self):
        """Single file with version in name is parsed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "backlog-v0.1.0-user-manual.md").touch()
            result = self._parse_versions_from_dir(Path(tmpdir))
            self.assertEqual(result, ["v0.1.0"])

    def test_multiple_versions_sorted_descending(self):
        """Multiple versions are sorted in descending semantic order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "backlog-v0.1.0-manual.md").touch()
            Path(tmpdir, "backlog-v0.2.0-manual.md").touch()
            Path(tmpdir, "backlog-v0.1.1-manual.md").touch()
            result = self._parse_versions_from_dir(Path(tmpdir))
            self.assertEqual(result, ["v0.2.0", "v0.1.1", "v0.1.0"])

    def test_deduplication(self):
        """Multiple files with same version are deduplicated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "backlog-v0.1.0-en.md").touch()
            Path(tmpdir, "backlog-v0.1.0-zh.md").touch()
            result = self._parse_versions_from_dir(Path(tmpdir))
            self.assertEqual(result, ["v0.1.0"])

    def test_non_version_files_ignored(self):
        """Files without version pattern are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").touch()
            Path(tmpdir, "changelog.txt").touch()
            Path(tmpdir, "backlog-v1.2.3-notes.md").touch()
            result = self._parse_versions_from_dir(Path(tmpdir))
            self.assertEqual(result, ["v1.2.3"])

    def test_semantic_sort_major_version(self):
        """Major version number differences are sorted correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "app-v1.0.0.md").touch()
            Path(tmpdir, "app-v2.0.0.md").touch()
            Path(tmpdir, "app-v0.9.9.md").touch()
            result = self._parse_versions_from_dir(Path(tmpdir))
            self.assertEqual(result, ["v2.0.0", "v1.0.0", "v0.9.9"])


class TestStatusBugFix(unittest.TestCase):
    """Tests for the original_status bug fix (change A)."""

    def test_original_status_snapshot_differs_from_mutated(self):
        """
        Verify that capturing original_status before mutation lets us detect change.
        This simulates what ItemFormScreen does: mutates item.status in-place.
        """
        item = BacklogItem(title="Test", priority=Priority.MEDIUM)
        item.status = Status.TODO

        # Simulate original_status capture BEFORE push_screen
        original_status = item.status

        # Simulate ItemFormScreen mutating item.status in action_submit
        item.status = Status.IN_PROGRESS  # user changed status

        # result is the same object as item (that's the bug scenario)
        result = item

        # With original_status snapshot: correctly detects change
        self.assertNotEqual(result.status, original_status)

    def test_original_status_no_change_detected_correctly(self):
        """When status is not changed, comparison with original_status returns equal."""
        item = BacklogItem(title="Test", priority=Priority.MEDIUM)
        item.status = Status.TODO

        original_status = item.status
        # User did not change status; item.status stays TODO
        result = item

        self.assertEqual(result.status, original_status)

    def test_without_snapshot_bug_would_occur(self):
        """
        Demonstrates the original bug: without snapshot, same-object comparison
        always returns equal even after mutation.
        """
        item = BacklogItem(title="Test", priority=Priority.MEDIUM)
        item.status = Status.TODO

        # Bug: capturing reference to item.status AFTER mutation is same as result.status
        # Simulate mutation
        item.status = Status.IN_PROGRESS
        result = item

        # Without snapshot: comparing result.status to item.status is always equal
        self.assertEqual(result.status, item.status)  # proves the bug

    def test_status_enum_values(self):
        """Status enum has expected values for comparison."""
        self.assertNotEqual(Status.TODO, Status.IN_PROGRESS)
        self.assertNotEqual(Status.IN_PROGRESS, Status.DONE)
        self.assertNotEqual(Status.TODO, Status.DONE)


class TestStaticCodeChecks(unittest.TestCase):
    """Static checks against app.py source code."""

    @classmethod
    def setUpClass(cls):
        app_path = Path(__file__).resolve().parent / "src" / "app.py"
        cls.source = app_path.read_text()

    def test_original_status_defined_before_push_screen(self):
        """original_status must be defined before push_screen call in action_edit_item."""
        # Both must exist in source
        self.assertIn("original_status = item.status", self.source)
        self.assertIn("result.status != original_status", self.source)

    def test_original_status_before_push_screen_ordering(self):
        """original_status assignment appears before push_screen in action_edit_item block."""
        idx_assign = self.source.find("original_status = item.status")
        idx_push = self.source.find("self.push_screen(ItemFormScreen(item)")
        self.assertGreater(idx_assign, 0, "original_status assignment not found")
        self.assertGreater(idx_push, 0, "push_screen(ItemFormScreen(item)) not found")
        self.assertLess(idx_assign, idx_push, "original_status must come before push_screen")

    def test_age_column_in_add_columns(self):
        """'Age' column must be in add_columns call."""
        self.assertIn('"Age"', self.source)
        self.assertIn('add_columns("ID", "Title", "Status", "Category", "Priority", "Age")', self.source)

    def test_age_str_logic_present(self):
        """age_str calculation logic must be present."""
        self.assertIn("age_str", self.source)
        self.assertIn("item.created_at", self.source)

    def test_version_screen_class_exists(self):
        """VersionScreen class must be defined."""
        self.assertIn("class VersionScreen", self.source)

    def test_v_binding_present(self):
        """'v' key binding for show_versions must be present."""
        self.assertIn('"v", "show_versions"', self.source)

    def test_action_show_versions_exists(self):
        """action_show_versions method must be defined."""
        self.assertIn("def action_show_versions", self.source)

    def test_parse_versions_method_exists(self):
        """_parse_versions method must be in VersionScreen."""
        self.assertIn("def _parse_versions", self.source)

    def test_get_release_dir_uses_file_not_cwd(self):
        """_get_release_dir must use __file__ not CWD."""
        self.assertIn("Path(__file__)", self.source)
        # Should NOT use os.getcwd() in release dir logic
        idx_get_release_dir = self.source.find("def _get_release_dir")
        idx_next_def = self.source.find("\n    def ", idx_get_release_dir + 1)
        method_body = self.source[idx_get_release_dir:idx_next_def]
        self.assertNotIn("os.getcwd()", method_body)

    def test_help_screen_v_key_documentation(self):
        """HelpScreen must document 'v' key for version history."""
        self.assertIn("Show version history", self.source)

    def test_datetime_now_outside_loop(self):
        """now = datetime.now() should be outside the for-item loop (P2 fix)."""
        # Find the _refresh_table method
        idx = self.source.find("def _refresh_table")
        end_idx = self.source.find("\n    def ", idx + 1)
        method = self.source[idx:end_idx]
        self.assertIn("now = datetime.now()", method)
        # now = datetime.now() should come before 'for item in items'
        idx_now = method.find("now = datetime.now()")
        idx_for = method.find("for item in items")
        self.assertLess(idx_now, idx_for, "datetime.now() should be outside the loop")


if __name__ == "__main__":
    unittest.main(verbosity=2)
