## [DEV-4-1] 实现三个功能改进

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-12T10:00:00

### 输入

读取了 `.cursor/agents/v0.2.0/tech-leader.log.md`，技术方案摘要：

1. **Bug A（状态保存不生效）**：`action_edit_item` 中，`ItemFormScreen.action_submit` 直接修改了传入的 `item` 对象（`self.item.status = status`），`dismiss(self.item)` 返回同一引用。回调中 `result.status != item.status` 永远为 `False`。修复方案：在 `push_screen` 前记录 `original_status = item.status`，回调中与快照比较。

2. **功能 B（Age 列）**：`BacklogItem.created_at` 已存储，无需改 model/repository。在列定义和行渲染中添加 `"Age"` 列，计算 `(datetime.now() - item.created_at).days`，`None` 时显示 `-`。

3. **功能 C（历史版本列表）**：新增 `VersionScreen` Modal，扫描 `release/` 目录，用正则 `v\d+\.\d+\.\d+` 提取版本号，去重、语义排序后展示。`BacklogApp` 新增快捷键 `v`。路径基于 `__file__` 定位，不依赖 CWD。

### 输出

**修改文件：** `.worktrees/v0.2.0/src/app.py`

---

#### 改动 A：修复状态保存 Bug

**原因：** 闭包捕获的 `item` 对象被 `ItemFormScreen` 内部直接修改，导致 `result` 与 `item` 指向同一对象，状态比较永远为 `False`。

```diff
+ import re
+ from datetime import datetime

  item = self.repo.get(item_id)
  if item is None:
      return
+ original_status = item.status

  def on_result(result):
      ...
-     if result.status != item.status:
+     if result.status != original_status:
          self.repo.transition_status(item_id, result.status)
```

---

#### 改动 B：添加 Age 列

**原因：** 用户需要直观看到每条记录的经过天数，辅助任务管理。

```diff
- table.add_columns("ID", "Title", "Status", "Category", "Priority")
+ table.add_columns("ID", "Title", "Status", "Category", "Priority", "Age")

  for item in items:
+     age_str = f"{(datetime.now() - item.created_at).days}d" if item.created_at else "-"
      table.add_row(
          str(item.id), item.title,
          STATUS_DISPLAY.get(item.status, item.status.value),
          item.category or "-",
          PRIORITY_DISPLAY.get(item.priority, item.priority.value),
+         age_str,
          key=str(item.id),
      )
```

---

#### 改动 C：新增 VersionScreen 和快捷键 `v`

**原因：** 用户需要在 TUI 中直接查看已发布的历史版本列表。

新增 `VersionScreen(ModalScreen[None])` 类：
- `_get_release_dir()`：返回 `Path(__file__).resolve().parent.parent / "release"`
- `_parse_versions()`：用正则 `v\d+\.\d+\.\d+` 从文件名提取版本，去重、语义降序排序
- `compose()`：DataTable 展示版本号列表
- `on_mount()`：填充版本数据，无版本时显示友好提示

`BacklogApp` 变更：
- `BINDINGS` 中新增 `Binding("v", "show_versions", "Versions")`
- 新增 `action_show_versions()` 方法，调用 `self.push_screen(VersionScreen())`

---

**验证：** `python -c "from app import BacklogApp, VersionScreen; print('Import OK')"` → 正常导入，无语法错误。

---

## [DEV-5-1] 修复 P1 问题：HelpScreen 添加 v 键说明

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-12T10:45:00

### 输入
CR-5-1 审查反馈：
- P1：`HelpScreen` 的 `Other` 区域未列出 `v` 键功能说明，用户按 `?` 无法发现版本历史功能。
- P2：`_refresh_table` 循环中每行调用 `datetime.now()`，建议提取到循环外缓存。

### 输出

**修改文件：** `.worktrees/v0.2.0/src/app.py`

---

#### 修复 P1：HelpScreen 添加 `v` 键说明

在 `HelpScreen.compose()` 的 `Other` 区域（`?` 键说明之前）新增一行：

```diff
  yield Label("[bold] Other[/bold]")
+ yield Label("   v              Show version history")
  yield Label("   ?              Show this help")
  yield Label("   q              Quit")
```

**原因：** `BacklogApp` 的 `BINDINGS` 已包含 `Binding("v", "show_versions", "Versions")`，但帮助屏幕未同步更新，导致用户按 `?` 时看不到该功能，影响可发现性。

---

#### 修复 P2：`datetime.now()` 提取到循环外

```diff
+ now = datetime.now()
  for item in items:
-     age_str = f"{(datetime.now() - item.created_at).days}d" if item.created_at else "-"
+     age_str = f"{(now - item.created_at).days}d" if item.created_at else "-"
```

**原因：** 每行重复调用 `datetime.now()` 存在微小时间漂移，提取到循环外语义更清晰，性能略有改善。

---
