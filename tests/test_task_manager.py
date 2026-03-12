"""
task_manager.py 的测试用例
"""

import json
import os
import sys
import tempfile
import unittest

# 将 src 目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import task_manager


class TestTaskManagerBase(unittest.TestCase):
    """测试基类，每个测试前重置全局状态"""

    def setUp(self):
        task_manager._reset()


class TestAddTask(TestTaskManagerBase):
    """测试 add_task 功能"""

    def test_add_basic_task(self):
        task = task_manager.add_task("测试任务")
        self.assertEqual(task["title"], "测试任务")
        self.assertEqual(task["description"], "")
        self.assertEqual(task["priority"], "medium")
        self.assertEqual(task["status"], "pending")
        self.assertIsNone(task["completed_at"])
        self.assertEqual(task["id"], 1)

    def test_add_task_with_all_fields(self):
        task = task_manager.add_task("任务A", "描述A", "high")
        self.assertEqual(task["title"], "任务A")
        self.assertEqual(task["description"], "描述A")
        self.assertEqual(task["priority"], "high")

    def test_add_multiple_tasks_increments_id(self):
        t1 = task_manager.add_task("任务1")
        t2 = task_manager.add_task("任务2")
        self.assertEqual(t1["id"], 1)
        self.assertEqual(t2["id"], 2)

    def test_add_task_strips_whitespace_title(self):
        task = task_manager.add_task("  空格标题  ")
        self.assertEqual(task["title"], "空格标题")

    def test_add_task_empty_title_raises(self):
        with self.assertRaises(ValueError):
            task_manager.add_task("")

    def test_add_task_whitespace_only_title_raises(self):
        with self.assertRaises(ValueError):
            task_manager.add_task("   ")

    def test_add_task_non_string_title_raises(self):
        with self.assertRaises(TypeError):
            task_manager.add_task(123)

    def test_add_task_invalid_priority_raises(self):
        with self.assertRaises(ValueError):
            task_manager.add_task("任务", priority="urgent")

    def test_add_task_all_valid_priorities(self):
        for p in ("high", "medium", "low"):
            task_manager._reset()
            task = task_manager.add_task("任务", priority=p)
            self.assertEqual(task["priority"], p)


class TestCompleteTask(TestTaskManagerBase):
    """测试 complete_task 功能"""

    def test_complete_existing_task(self):
        task_manager.add_task("任务1")
        result = task_manager.complete_task(1)
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "completed")
        self.assertIsNotNone(result["completed_at"])

    def test_complete_nonexistent_task_returns_none(self):
        result = task_manager.complete_task(999)
        self.assertIsNone(result)

    def test_complete_already_completed_task_preserves_timestamp(self):
        """重复完成同一任务不应更新 completed_at"""
        task_manager.add_task("任务1")
        first = task_manager.complete_task(1)
        original_time = first["completed_at"]
        second = task_manager.complete_task(1)
        self.assertEqual(second["completed_at"], original_time)


class TestDeleteTask(TestTaskManagerBase):
    """测试 delete_task 功能"""

    def test_delete_existing_task(self):
        task_manager.add_task("任务1")
        task_manager.add_task("任务2")
        removed = task_manager.delete_task(1)
        self.assertIsNotNone(removed)
        self.assertEqual(removed["id"], 1)
        self.assertEqual(len(task_manager.get_tasks()), 1)

    def test_delete_nonexistent_task_returns_none(self):
        result = task_manager.delete_task(999)
        self.assertIsNone(result)

    def test_delete_only_task(self):
        task_manager.add_task("唯一任务")
        removed = task_manager.delete_task(1)
        self.assertIsNotNone(removed)
        self.assertEqual(len(task_manager.get_tasks()), 0)


class TestGetTasks(TestTaskManagerBase):
    """测试 get_tasks 功能"""

    def test_get_all_tasks(self):
        task_manager.add_task("任务1")
        task_manager.add_task("任务2")
        result = task_manager.get_tasks()
        self.assertEqual(len(result), 2)

    def test_get_tasks_returns_copy(self):
        task_manager.add_task("任务1")
        result = task_manager.get_tasks()
        result.append({"fake": True})
        self.assertEqual(len(task_manager.get_tasks()), 1)

    def test_get_tasks_filter_by_status(self):
        task_manager.add_task("任务1")
        task_manager.add_task("任务2")
        task_manager.complete_task(1)
        pending = task_manager.get_tasks(status="pending")
        completed = task_manager.get_tasks(status="completed")
        self.assertEqual(len(pending), 1)
        self.assertEqual(len(completed), 1)

    def test_get_tasks_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            task_manager.get_tasks(status="invalid")

    def test_get_tasks_empty(self):
        result = task_manager.get_tasks()
        self.assertEqual(result, [])


class TestGetTaskById(TestTaskManagerBase):
    """测试 get_task_by_id 功能"""

    def test_get_existing_task(self):
        task_manager.add_task("任务1")
        result = task_manager.get_task_by_id(1)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "任务1")

    def test_get_nonexistent_task(self):
        result = task_manager.get_task_by_id(999)
        self.assertIsNone(result)


class TestUpdateTask(TestTaskManagerBase):
    """测试 update_task 功能"""

    def test_update_title(self):
        task_manager.add_task("旧标题")
        result = task_manager.update_task(1, title="新标题")
        self.assertEqual(result["title"], "新标题")

    def test_update_description_to_empty_string(self):
        """修复：旧版本使用 if description 导致无法设为空字符串"""
        task_manager.add_task("任务", "原描述")
        result = task_manager.update_task(1, description="")
        self.assertEqual(result["description"], "")

    def test_update_priority(self):
        task_manager.add_task("任务")
        result = task_manager.update_task(1, priority="high")
        self.assertEqual(result["priority"], "high")

    def test_update_invalid_priority_raises(self):
        task_manager.add_task("任务")
        with self.assertRaises(ValueError):
            task_manager.update_task(1, priority="urgent")

    def test_update_empty_title_raises(self):
        task_manager.add_task("任务")
        with self.assertRaises(ValueError):
            task_manager.update_task(1, title="")

    def test_update_nonexistent_task_returns_none(self):
        result = task_manager.update_task(999, title="新标题")
        self.assertIsNone(result)

    def test_update_no_changes(self):
        task_manager.add_task("任务")
        result = task_manager.update_task(1)
        self.assertEqual(result["title"], "任务")


class TestSaveLoadTasks(TestTaskManagerBase):
    """测试 save_tasks 和 load_tasks 功能"""

    def test_save_and_load(self):
        task_manager.add_task("任务1", "描述1", "high")
        task_manager.add_task("任务2")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmpfile = f.name

        try:
            task_manager.save_tasks(tmpfile)
            task_manager._reset()
            task_manager.load_tasks(tmpfile)

            result = task_manager.get_tasks()
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["title"], "任务1")
            self.assertEqual(task_manager.task_id_counter, 2)
        finally:
            os.unlink(tmpfile)

    def test_load_nonexistent_file_does_nothing(self):
        task_manager.load_tasks("nonexistent_file_12345.json")
        self.assertEqual(len(task_manager.get_tasks()), 0)

    def test_load_invalid_json_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("not valid json{{{")
            tmpfile = f.name
        try:
            with self.assertRaises(json.JSONDecodeError):
                task_manager.load_tasks(tmpfile)
        finally:
            os.unlink(tmpfile)

    def test_load_non_list_json_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({"not": "a list"}, f)
            tmpfile = f.name
        try:
            with self.assertRaises(ValueError):
                task_manager.load_tasks(tmpfile)
        finally:
            os.unlink(tmpfile)

    def test_load_list_with_invalid_items_raises(self):
        """加载的任务记录缺少 id 字段时应报错"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump([{"title": "no id field"}], f)
            tmpfile = f.name
        try:
            with self.assertRaises(ValueError):
                task_manager.load_tasks(tmpfile)
        finally:
            os.unlink(tmpfile)

    def test_load_list_with_non_dict_items_raises(self):
        """加载的任务记录不是字典时应报错"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(["not a dict", 123], f)
            tmpfile = f.name
        try:
            with self.assertRaises(ValueError):
                task_manager.load_tasks(tmpfile)
        finally:
            os.unlink(tmpfile)

    def test_save_uses_utf8(self):
        task_manager.add_task("中文任务")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmpfile = f.name
        try:
            task_manager.save_tasks(tmpfile)
            with open(tmpfile, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("中文任务", content)
        finally:
            os.unlink(tmpfile)


class TestGetStats(TestTaskManagerBase):
    """测试 get_stats 功能"""

    def test_stats_empty(self):
        stats = task_manager.get_stats()
        self.assertEqual(stats, {"total": 0, "completed": 0, "pending": 0})

    def test_stats_with_tasks(self):
        task_manager.add_task("任务1")
        task_manager.add_task("任务2")
        task_manager.complete_task(1)
        stats = task_manager.get_stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["pending"], 1)


class TestSearchTasks(TestTaskManagerBase):
    """测试 search_tasks 功能"""

    def test_search_by_title(self):
        task_manager.add_task("Python学习", "内容")
        task_manager.add_task("Java学习", "内容")
        results = task_manager.search_tasks("Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Python学习")

    def test_search_by_description(self):
        task_manager.add_task("任务", "包含关键词ABC的描述")
        results = task_manager.search_tasks("ABC")
        self.assertEqual(len(results), 1)

    def test_search_case_insensitive(self):
        task_manager.add_task("Python Task")
        results = task_manager.search_tasks("python")
        self.assertEqual(len(results), 1)

    def test_search_no_results(self):
        task_manager.add_task("任务1")
        results = task_manager.search_tasks("不存在")
        self.assertEqual(len(results), 0)

    def test_search_empty_keyword_returns_all(self):
        task_manager.add_task("任务1")
        task_manager.add_task("任务2")
        results = task_manager.search_tasks("")
        self.assertEqual(len(results), 2)

    def test_search_non_string_raises(self):
        with self.assertRaises(TypeError):
            task_manager.search_tasks(123)


if __name__ == "__main__":
    unittest.main()
