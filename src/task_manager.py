"""
简单的任务管理器 - 用于演示 Claude Code 多 Agent 协同工作
"""

import json
import os
from datetime import datetime

VALID_PRIORITIES = ("high", "medium", "low")
VALID_STATUSES = ("pending", "completed")

# 全局变量存储任务
tasks = []
task_id_counter = 0


def _reset():
    """重置全局状态（仅用于测试）"""
    global tasks, task_id_counter
    tasks = []
    task_id_counter = 0


def add_task(title, description="", priority="medium"):
    """添加新任务

    Args:
        title: 任务标题，不能为空
        description: 任务描述
        priority: 优先级，可选 "high"、"medium"、"low"

    Returns:
        新创建的任务字典

    Raises:
        ValueError: 标题为空或优先级无效时
        TypeError: 参数类型不正确时
    """
    global task_id_counter

    if not isinstance(title, str):
        raise TypeError("标题必须是字符串")
    if not title.strip():
        raise ValueError("标题不能为空")
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"无效的优先级 '{priority}'，可选值: {VALID_PRIORITIES}")

    task_id_counter += 1
    task = {
        "id": task_id_counter,
        "title": title.strip(),
        "description": description if isinstance(description, str) else str(description),
        "priority": priority,
        "status": "pending",
        "created_at": str(datetime.now()),
        "completed_at": None,
    }
    tasks.append(task)
    return task


def complete_task(task_id):
    """完成任务

    Args:
        task_id: 任务 ID

    Returns:
        完成的任务字典，如果未找到则返回 None
    """
    task = get_task_by_id(task_id)
    if task is None:
        return None
    if task["status"] == "completed":
        return task
    task["status"] = "completed"
    task["completed_at"] = str(datetime.now())
    return task


def delete_task(task_id):
    """删除任务

    Args:
        task_id: 任务 ID

    Returns:
        被删除的任务字典，如果未找到则返回 None
    """
    global tasks
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            return tasks.pop(i)
    return None


def get_tasks(status=None):
    """获取任务列表

    Args:
        status: 可选的状态过滤器 ("pending" 或 "completed")

    Returns:
        任务列表的副本
    """
    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"无效的状态 '{status}'，可选值: {VALID_STATUSES}")
        return [t for t in tasks if t["status"] == status]
    return list(tasks)


def get_task_by_id(task_id):
    """根据ID获取任务

    Args:
        task_id: 任务 ID

    Returns:
        匹配的任务字典，如果未找到则返回 None
    """
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def update_task(task_id, title=None, description=None, priority=None):
    """更新任务

    Args:
        task_id: 任务 ID
        title: 新标题（None 表示不修改）
        description: 新描述（None 表示不修改）
        priority: 新优先级（None 表示不修改）

    Returns:
        更新后的任务字典，如果未找到则返回 None

    Raises:
        ValueError: 标题为空或优先级无效时
    """
    task = get_task_by_id(task_id)
    if task is None:
        return None

    if title is not None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("标题不能为空")
        task["title"] = title.strip()
    if description is not None:
        task["description"] = description
    if priority is not None:
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"无效的优先级 '{priority}'，可选值: {VALID_PRIORITIES}")
        task["priority"] = priority
    return task


def save_tasks(filename="tasks.json"):
    """保存任务到文件

    Args:
        filename: 文件路径

    Raises:
        OSError: 文件写入失败时
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise OSError(f"保存任务失败: {e}") from e


def load_tasks(filename="tasks.json"):
    """从文件加载任务

    Args:
        filename: 文件路径

    Raises:
        json.JSONDecodeError: JSON 格式错误时
        OSError: 文件读取失败时
    """
    global tasks, task_id_counter
    if not os.path.exists(filename):
        return
    try:
        with open(filename, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"任务文件格式错误: {e.msg}", e.doc, e.pos) from e
    except OSError as e:
        raise OSError(f"加载任务失败: {e}") from e

    if not isinstance(loaded, list):
        raise ValueError("任务文件内容格式不正确，应为列表")

    for i, item in enumerate(loaded):
        if not isinstance(item, dict) or "id" not in item:
            raise ValueError(f"任务文件第 {i} 条记录格式不正确，缺少必要字段")

    tasks = loaded
    if tasks:
        task_id_counter = max(t["id"] for t in tasks)


def get_stats():
    """获取统计信息

    Returns:
        包含 total、completed、pending 的统计字典
    """
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "completed")
    pending = total - completed
    return {"total": total, "completed": completed, "pending": pending}


def search_tasks(keyword):
    """搜索任务

    Args:
        keyword: 搜索关键词

    Returns:
        匹配的任务列表

    Raises:
        TypeError: keyword 不是字符串时
    """
    if not isinstance(keyword, str):
        raise TypeError("搜索关键词必须是字符串")
    if not keyword.strip():
        return list(tasks)

    keyword_lower = keyword.lower()
    return [
        task for task in tasks
        if keyword_lower in task["title"].lower()
        or keyword_lower in task["description"].lower()
    ]


if __name__ == "__main__":
    # 简单测试
    add_task("学习 Python", "完成 Python 基础教程", "high")
    add_task("写文档", "编写项目文档")
    add_task("代码审查", "审查团队代码", "low")

    print("所有任务:", get_tasks())
    print("统计:", get_stats())

    complete_task(1)
    print("完成任务1后:", get_stats())

    print("搜索'Python':", search_tasks("Python"))
