"""Tests for src/repository.py — BacklogRepository with in-memory SQLite."""

import sys
import os
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import BacklogItem, Priority, Status
from repository import BacklogRepository


class TestBacklogRepository(unittest.TestCase):
    def setUp(self):
        self.repo = BacklogRepository(":memory:")

    def tearDown(self):
        self.repo.close()

    # --- Create ---
    def test_create_assigns_id(self):
        item = self.repo.create(BacklogItem(title="First"))
        self.assertIsNotNone(item.id)
        self.assertEqual(item.id, 1)

    def test_create_multiple(self):
        self.repo.create(BacklogItem(title="A"))
        item = self.repo.create(BacklogItem(title="B"))
        self.assertEqual(item.id, 2)

    # --- Get ---
    def test_get_existing(self):
        created = self.repo.create(BacklogItem(title="G"))
        fetched = self.repo.get(created.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "G")

    def test_get_nonexistent(self):
        self.assertIsNone(self.repo.get(999))

    # --- List ---
    def test_list_all(self):
        self.repo.create(BacklogItem(title="A"))
        self.repo.create(BacklogItem(title="B"))
        self.assertEqual(len(self.repo.list()), 2)

    def test_list_filter_status(self):
        self.repo.create(BacklogItem(title="A", status=Status.TODO))
        self.repo.create(BacklogItem(title="B", status=Status.DONE))
        result = self.repo.list(status=Status.TODO)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "A")

    def test_list_filter_category(self):
        self.repo.create(BacklogItem(title="A", category="frontend"))
        self.repo.create(BacklogItem(title="B", category="backend"))
        result = self.repo.list(category="frontend")
        self.assertEqual(len(result), 1)

    def test_list_filter_keyword(self):
        self.repo.create(BacklogItem(title="Login bug"))
        self.repo.create(BacklogItem(title="Signup feature", description="new login flow"))
        result = self.repo.list(keyword="login")
        self.assertEqual(len(result), 2)

    def test_list_empty(self):
        self.assertEqual(self.repo.list(), [])

    # --- Update ---
    def test_update_title(self):
        item = self.repo.create(BacklogItem(title="Old"))
        updated = self.repo.update(item.id, title="New")
        self.assertEqual(updated.title, "New")

    def test_update_status_enum(self):
        item = self.repo.create(BacklogItem(title="X"))
        updated = self.repo.update(item.id, status=Status.DONE)
        self.assertEqual(updated.status, Status.DONE)

    def test_update_priority_enum(self):
        item = self.repo.create(BacklogItem(title="X"))
        updated = self.repo.update(item.id, priority=Priority.HIGH)
        self.assertEqual(updated.priority, Priority.HIGH)

    def test_update_nonexistent(self):
        self.assertIsNone(self.repo.update(999, title="X"))

    def test_update_ignores_unknown_fields(self):
        item = self.repo.create(BacklogItem(title="X"))
        updated = self.repo.update(item.id, unknown_field="val")
        self.assertEqual(updated.title, "X")

    def test_update_no_fields(self):
        item = self.repo.create(BacklogItem(title="X"))
        updated = self.repo.update(item.id)
        self.assertEqual(updated.title, "X")

    # --- Delete ---
    def test_delete_existing(self):
        item = self.repo.create(BacklogItem(title="D"))
        self.assertTrue(self.repo.delete(item.id))
        self.assertIsNone(self.repo.get(item.id))

    def test_delete_nonexistent(self):
        self.assertFalse(self.repo.delete(999))

    # --- Transition Status ---
    def test_transition_todo_to_in_progress(self):
        item = self.repo.create(BacklogItem(title="T", status=Status.TODO))
        result = self.repo.transition_status(item.id, Status.IN_PROGRESS)
        self.assertEqual(result.status, Status.IN_PROGRESS)

    def test_transition_in_progress_to_done(self):
        item = self.repo.create(BacklogItem(title="T", status=Status.TODO))
        self.repo.transition_status(item.id, Status.IN_PROGRESS)
        result = self.repo.transition_status(item.id, Status.DONE)
        self.assertEqual(result.status, Status.DONE)

    def test_transition_in_progress_to_todo(self):
        item = self.repo.create(BacklogItem(title="T", status=Status.TODO))
        self.repo.transition_status(item.id, Status.IN_PROGRESS)
        result = self.repo.transition_status(item.id, Status.TODO)
        self.assertEqual(result.status, Status.TODO)

    def test_transition_done_to_in_progress(self):
        item = self.repo.create(BacklogItem(title="T", status=Status.TODO))
        self.repo.transition_status(item.id, Status.IN_PROGRESS)
        self.repo.transition_status(item.id, Status.DONE)
        result = self.repo.transition_status(item.id, Status.IN_PROGRESS)
        self.assertEqual(result.status, Status.IN_PROGRESS)

    def test_transition_invalid_todo_to_done(self):
        item = self.repo.create(BacklogItem(title="T", status=Status.TODO))
        with self.assertRaises(ValueError):
            self.repo.transition_status(item.id, Status.DONE)

    def test_transition_invalid_done_to_todo(self):
        item = self.repo.create(BacklogItem(title="T", status=Status.TODO))
        self.repo.transition_status(item.id, Status.IN_PROGRESS)
        self.repo.transition_status(item.id, Status.DONE)
        with self.assertRaises(ValueError):
            self.repo.transition_status(item.id, Status.TODO)

    def test_transition_nonexistent(self):
        self.assertIsNone(self.repo.transition_status(999, Status.IN_PROGRESS))

    # --- Categories ---
    def test_get_categories(self):
        self.repo.create(BacklogItem(title="A", category="frontend"))
        self.repo.create(BacklogItem(title="B", category="backend"))
        self.repo.create(BacklogItem(title="C", category=""))
        cats = self.repo.get_categories()
        self.assertEqual(cats, ["backend", "frontend"])

    def test_get_categories_empty(self):
        self.assertEqual(self.repo.get_categories(), [])

    # --- Stats ---
    def test_get_stats(self):
        self.repo.create(BacklogItem(title="A", status=Status.TODO, priority=Priority.HIGH))
        self.repo.create(BacklogItem(title="B", status=Status.TODO, priority=Priority.LOW))
        self.repo.create(BacklogItem(title="C", status=Status.DONE, priority=Priority.HIGH))
        stats = self.repo.get_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_status"]["todo"], 2)
        self.assertEqual(stats["by_status"]["done"], 1)
        self.assertEqual(stats["by_priority"]["high"], 2)

    def test_get_stats_with_category_filter(self):
        self.repo.create(BacklogItem(title="A", category="fe"))
        self.repo.create(BacklogItem(title="B", category="be"))
        stats = self.repo.get_stats(category="fe")
        self.assertEqual(stats["total"], 1)

    def test_get_stats_empty(self):
        stats = self.repo.get_stats()
        self.assertEqual(stats["total"], 0)

    # --- Context Manager ---
    def test_context_manager(self):
        with BacklogRepository(":memory:") as repo:
            repo.create(BacklogItem(title="CM"))
            self.assertEqual(len(repo.list()), 1)


class TestSoftDeleteAndTrash(unittest.TestCase):
    """Tests for soft-delete, restore, hard_delete, list_trash (v0.1.0)."""

    def setUp(self):
        self.repo = BacklogRepository(":memory:")

    def tearDown(self):
        self.repo.close()

    # --- Soft delete (delete()) ---
    def test_delete_returns_true(self):
        item = self.repo.create(BacklogItem(title="D"))
        self.assertTrue(self.repo.delete(item.id))

    def test_delete_makes_get_return_none(self):
        item = self.repo.create(BacklogItem(title="D"))
        self.repo.delete(item.id)
        self.assertIsNone(self.repo.get(item.id))

    def test_delete_item_retrievable_with_include_deleted(self):
        item = self.repo.create(BacklogItem(title="D"))
        self.repo.delete(item.id)
        found = self.repo.get(item.id, include_deleted=True)
        self.assertIsNotNone(found)
        self.assertEqual(found.title, "D")

    def test_delete_sets_deleted_at(self):
        item = self.repo.create(BacklogItem(title="D"))
        self.repo.delete(item.id)
        found = self.repo.get(item.id, include_deleted=True)
        self.assertIsNotNone(found.deleted_at)

    def test_delete_sets_expires_at_180_days(self):
        item = self.repo.create(BacklogItem(title="D"))
        self.repo.delete(item.id)
        found = self.repo.get(item.id, include_deleted=True)
        self.assertIsNotNone(found.expires_at)
        delta = found.expires_at - found.deleted_at
        self.assertAlmostEqual(delta.days, 180, delta=1)

    def test_delete_nonexistent_returns_false(self):
        self.assertFalse(self.repo.delete(999))

    def test_delete_already_deleted_returns_false(self):
        item = self.repo.create(BacklogItem(title="D"))
        self.repo.delete(item.id)
        self.assertFalse(self.repo.delete(item.id))

    # --- list() excludes deleted ---
    def test_list_excludes_deleted(self):
        item = self.repo.create(BacklogItem(title="A"))
        self.repo.create(BacklogItem(title="B"))
        self.repo.delete(item.id)
        result = self.repo.list()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "B")

    def test_list_empty_after_all_deleted(self):
        item = self.repo.create(BacklogItem(title="A"))
        self.repo.delete(item.id)
        self.assertEqual(self.repo.list(), [])

    # --- list_trash() ---
    def test_list_trash_returns_deleted_items(self):
        item = self.repo.create(BacklogItem(title="T"))
        self.repo.delete(item.id)
        trash = self.repo.list_trash()
        self.assertEqual(len(trash), 1)
        self.assertEqual(trash[0].title, "T")

    def test_list_trash_empty_when_nothing_deleted(self):
        self.repo.create(BacklogItem(title="A"))
        self.assertEqual(self.repo.list_trash(), [])

    def test_list_trash_excludes_expired(self):
        item = self.repo.create(BacklogItem(title="Expired"))
        self.repo.delete(item.id)
        # Manually set expires_at to the past
        past = (datetime.now() - timedelta(days=1)).isoformat()
        self.repo._conn.execute(
            "UPDATE backlog_items SET expires_at = ? WHERE id = ?",
            (past, item.id),
        )
        self.repo._conn.commit()
        trash = self.repo.list_trash()
        self.assertEqual(len(trash), 0)

    def test_list_trash_newest_first(self):
        item1 = self.repo.create(BacklogItem(title="First"))
        item2 = self.repo.create(BacklogItem(title="Second"))
        self.repo.delete(item1.id)
        self.repo.delete(item2.id)
        trash = self.repo.list_trash()
        self.assertEqual(len(trash), 2)
        # Second was deleted after first, so it should appear first
        self.assertEqual(trash[0].title, "Second")

    # --- restore() ---
    def test_restore_returns_item(self):
        item = self.repo.create(BacklogItem(title="R"))
        self.repo.delete(item.id)
        restored = self.repo.restore(item.id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.title, "R")

    def test_restore_clears_deleted_at(self):
        item = self.repo.create(BacklogItem(title="R"))
        self.repo.delete(item.id)
        self.repo.restore(item.id)
        found = self.repo.get(item.id)
        self.assertIsNotNone(found)
        self.assertIsNone(found.deleted_at)

    def test_restore_clears_expires_at(self):
        item = self.repo.create(BacklogItem(title="R"))
        self.repo.delete(item.id)
        self.repo.restore(item.id)
        found = self.repo.get(item.id)
        self.assertIsNone(found.expires_at)

    def test_restore_item_appears_in_list(self):
        item = self.repo.create(BacklogItem(title="R"))
        self.repo.delete(item.id)
        self.repo.restore(item.id)
        result = self.repo.list()
        self.assertEqual(len(result), 1)

    def test_restore_nonexistent_returns_none(self):
        self.assertIsNone(self.repo.restore(999))

    def test_restore_non_deleted_returns_none(self):
        item = self.repo.create(BacklogItem(title="R"))
        self.assertIsNone(self.repo.restore(item.id))

    # --- hard_delete() ---
    def test_hard_delete_returns_true(self):
        item = self.repo.create(BacklogItem(title="H"))
        self.assertTrue(self.repo.hard_delete(item.id))

    def test_hard_delete_removes_record_permanently(self):
        item = self.repo.create(BacklogItem(title="H"))
        self.repo.hard_delete(item.id)
        self.assertIsNone(self.repo.get(item.id, include_deleted=True))

    def test_hard_delete_nonexistent_returns_false(self):
        self.assertFalse(self.repo.hard_delete(999))

    def test_hard_delete_soft_deleted_item(self):
        item = self.repo.create(BacklogItem(title="H"))
        self.repo.delete(item.id)
        self.assertTrue(self.repo.hard_delete(item.id))
        self.assertIsNone(self.repo.get(item.id, include_deleted=True))

    # --- _purge_expired() ---
    def test_purge_expired_removes_past_expires(self):
        item = self.repo.create(BacklogItem(title="Old"))
        self.repo.delete(item.id)
        past = (datetime.now() - timedelta(days=1)).isoformat()
        self.repo._conn.execute(
            "UPDATE backlog_items SET expires_at = ? WHERE id = ?",
            (past, item.id),
        )
        self.repo._conn.commit()
        self.repo._purge_expired()
        self.assertIsNone(self.repo.get(item.id, include_deleted=True))

    def test_purge_expired_keeps_future_expires(self):
        item = self.repo.create(BacklogItem(title="Recent"))
        self.repo.delete(item.id)
        self.repo._purge_expired()
        self.assertIsNotNone(self.repo.get(item.id, include_deleted=True))

    # --- _migrate_schema() idempotent ---
    def test_migrate_schema_idempotent(self):
        # Calling a second time should not raise or add duplicate columns
        try:
            self.repo._migrate_schema()
        except Exception as e:
            self.fail(f"_migrate_schema() raised on second call: {e}")

    # --- get_categories() excludes deleted ---
    def test_get_categories_excludes_deleted(self):
        item = self.repo.create(BacklogItem(title="A", category="frontend"))
        self.repo.create(BacklogItem(title="B", category="backend"))
        self.repo.delete(item.id)
        cats = self.repo.get_categories()
        self.assertEqual(cats, ["backend"])
        self.assertNotIn("frontend", cats)

    # --- get_stats() excludes deleted ---
    def test_get_stats_excludes_deleted(self):
        item = self.repo.create(BacklogItem(title="A"))
        self.repo.create(BacklogItem(title="B"))
        self.repo.delete(item.id)
        stats = self.repo.get_stats()
        self.assertEqual(stats["total"], 1)

    def test_get_stats_with_category_excludes_deleted(self):
        item = self.repo.create(BacklogItem(title="A", category="fe"))
        self.repo.create(BacklogItem(title="B", category="fe"))
        self.repo.delete(item.id)
        stats = self.repo.get_stats(category="fe")
        self.assertEqual(stats["total"], 1)


class TestPaginationAndCount(unittest.TestCase):
    """Tests for list() limit/offset and count() — v0.2.0 new features."""

    def setUp(self):
        self.repo = BacklogRepository(":memory:")

    def tearDown(self):
        self.repo.close()

    def _create_items(self, n: int):
        for i in range(n):
            self.repo.create(BacklogItem(title=f"Item {i+1}"))

    # --- list() with limit/offset ---

    def test_list_with_limit(self):
        self._create_items(5)
        result = self.repo.list(limit=2)
        self.assertEqual(len(result), 2)

    def test_list_with_offset(self):
        self._create_items(5)
        result = self.repo.list(limit=2, offset=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].title, "Item 3")
        self.assertEqual(result[1].title, "Item 4")

    def test_list_with_limit_exceeding(self):
        self._create_items(5)
        result = self.repo.list(limit=100)
        self.assertEqual(len(result), 5)

    def test_list_without_limit_backward_compat(self):
        self._create_items(5)
        result = self.repo.list()
        self.assertEqual(len(result), 5)

    # --- count() ---

    def test_count_all(self):
        self._create_items(3)
        self.assertEqual(self.repo.count(), 3)

    def test_count_with_status_filter(self):
        self.repo.create(BacklogItem(title="A", status=Status.TODO))
        self.repo.create(BacklogItem(title="B", status=Status.TODO))
        self.repo.create(BacklogItem(title="C", status=Status.DONE))
        self.assertEqual(self.repo.count(status=Status.TODO), 2)
        self.assertEqual(self.repo.count(status=Status.DONE), 1)

    def test_count_with_keyword_filter(self):
        self.repo.create(BacklogItem(title="Login bug"))
        self.repo.create(BacklogItem(title="Signup feature", description="new login flow"))
        self.repo.create(BacklogItem(title="Other task"))
        self.assertEqual(self.repo.count(keyword="login"), 2)
        self.assertEqual(self.repo.count(keyword="other"), 1)

    def test_count_excludes_deleted(self):
        item = self.repo.create(BacklogItem(title="A"))
        self.repo.create(BacklogItem(title="B"))
        self.repo.delete(item.id)
        self.assertEqual(self.repo.count(), 1)

    # --- list_trash() extended tests ---

    def _create_and_delete(self, title: str, description: str = "") -> "BacklogItem":
        item = self.repo.create(BacklogItem(title=title, description=description))
        self.repo.delete(item.id)
        return item

    def test_list_trash_with_keyword(self):
        self._create_and_delete("Login bug")
        self._create_and_delete("Signup feature")
        result = self.repo.list_trash(keyword="login")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Login bug")

    def test_list_trash_with_keyword_description(self):
        self._create_and_delete("Signup feature", description="new login flow")
        self._create_and_delete("Other task")
        result = self.repo.list_trash(keyword="login")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Signup feature")

    def test_list_trash_with_keyword_no_match(self):
        self._create_and_delete("Login bug")
        result = self.repo.list_trash(keyword="nonexistent")
        self.assertEqual(result, [])

    def test_list_trash_with_limit_offset(self):
        for i in range(5):
            self._create_and_delete(f"Trash item {i+1}")
        result_first = self.repo.list_trash(limit=2, offset=0)
        result_second = self.repo.list_trash(limit=2, offset=2)
        self.assertEqual(len(result_first), 2)
        self.assertEqual(len(result_second), 2)
        # Ensure no overlap
        titles_first = {r.title for r in result_first}
        titles_second = {r.title for r in result_second}
        self.assertEqual(len(titles_first & titles_second), 0)

    def test_list_trash_backward_compat(self):
        self._create_and_delete("A")
        self._create_and_delete("B")
        result = self.repo.list_trash()
        self.assertEqual(len(result), 2)

    # --- count_trash() ---

    def test_count_trash_all(self):
        self._create_and_delete("A")
        self._create_and_delete("B")
        self._create_and_delete("C")
        self.assertEqual(self.repo.count_trash(), 3)

    def test_count_trash_with_keyword(self):
        self._create_and_delete("Login bug")
        self._create_and_delete("Signup feature", description="new login flow")
        self._create_and_delete("Other task")
        self.assertEqual(self.repo.count_trash(keyword="login"), 2)
        self.assertEqual(self.repo.count_trash(keyword="other"), 1)

    def test_count_trash_excludes_non_deleted(self):
        self.repo.create(BacklogItem(title="Active"))
        self._create_and_delete("Deleted")
        self.assertEqual(self.repo.count_trash(), 1)


if __name__ == "__main__":
    unittest.main()
