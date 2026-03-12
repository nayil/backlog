## [CUST-7-1] 客户验收报告：v0.1.0 删除二次确认与回收站功能

- **阶段：** 7
- **状态：** completed
- **时间：** 2026-03-12T04:00:00

### 输入

需求描述：
1. 当用户删除时，需要二次确认
2. 支持回收站功能，用户删除的内容自动进入回收站；进入回收站的内容最大保留期为180天；在保留期内，用户可以恢复被删除的内容

读取来源：
- `project-manager.log.md`（PM-7-1）：确认版本 v0.1.0 所有阶段完成，148 个测试全部通过，可正式发布
- `src/repository.py`：软删除存储层实现
- `src/app.py`：TUI 二次确认弹窗与回收站界面实现

### 输出

---

## 验收执行摘要

| 验收项 | 验收方式 | 结论 |
|--------|----------|------|
| 源码审查：删除二次确认 | 阅读 `app.py` | 通过 |
| 源码审查：回收站存储层 | 阅读 `repository.py` | 通过 |
| 单元测试全量运行 | `pytest tests/ -v` | **148/148 全部通过** |
| 功能验收脚本 | 自定义 Python 脚本 | **8/8 测试通过** |

---

## 需求一：删除二次确认

### 代码审查结论

`app.py` 中 `action_delete_item()` 实现符合需求：
- 按 `d` 键触发删除时，先调用 `self.push_screen(ConfirmDeleteScreen(item.title), callback=on_confirmed)` 弹出确认对话框
- `ConfirmDeleteScreen` 显示条目标题及提示文案 "Move to Trash? — The item will be moved to trash and can be restored within 180 days."
- 按 `y` 或 `Enter` 确认后才执行 `repo.delete()`；按 `n` 或 `Esc` 取消，不执行任何操作
- 回收站内永久删除（`x` 键）同样触发带 `permanent=True` 的 `ConfirmDeleteScreen`，显示 "Delete Forever? — This action cannot be undone."

**结论：需求一满足。**

---

## 需求二：回收站功能

### 代码审查结论

`repository.py` 软删除实现完整：
- `delete(item_id)`：软删除，写入 `deleted_at=now`, `expires_at=now+180天`，不物理删除
- `list()`：默认添加 `WHERE deleted_at IS NULL`，已删除条目对主界面不可见
- `list_trash()`：返回 `deleted_at IS NOT NULL AND expires_at > now` 的条目，即未过期的回收站条目
- `restore(item_id)`：清空 `deleted_at` 和 `expires_at`，条目重新回到主列表
- `_purge_expired()`：在 `__init__` 时自动执行，物理删除 `expires_at <= now` 的条目
- `hard_delete(item_id)`：物理删除，供回收站永久删除操作使用

### 功能验收脚本结果（8 项全部通过）

```
[PASS] 1. 创建 item：id=1, title='Test Task'
[PASS] 2. list() 返回活跃条目（count=1）
[PASS] 3. delete() 软删除成功（返回 True）
[PASS] 4. list() 排除已删除条目（count=0）
[PASS] 5. list_trash() 包含已删除条目，expires_at = deleted_at + 180 天
[PASS] 6. restore() 成功恢复，条目重新出现在 list()，从 list_trash() 移除
[PASS] 7. 超过 180 天的条目被 _purge_expired() 物理清除
[PASS] 8. hard_delete() 永久删除，DB 中不再存在该条目
```

**结论：需求二满足。**

---

## 单元测试结果

```
pytest tests/ -v
148 passed in 0.19s
```

- 新增测试：42 个（13 个 models + 29 个 repository）
- 全量回归：148/148，失败 0
- 覆盖核心场景：软删除、恢复、永久删除、过期清理、schema 迁移幂等性、主界面过滤

---

## 已知限制（不影响验收结论）

1. TUI 层（`ConfirmDeleteScreen`、`TrashScreen`）无自动化测试，仅源码审查验证逻辑正确性
2. `deleted_at` / `expires_at` 使用 naive datetime（本地时间），跨时区场景下 180 天计算可能有轻微偏差
3. `_purge_expired()` 在 Repository 初始化时同步执行，数据量极大时可能轻微影响启动速度

---

## 验收结论

**通过**

v0.1.0 两项功能需求均已实现：
- 删除操作触发二次确认弹窗，用户明确确认后才执行软删除
- 回收站功能完整：自动进入回收站、180 天保留期、保留期内可恢复、超期自动清理

---

## [CUST-7-2] 客户验收报告：v0.2.0 查看使用帮助功能

- **阶段：** 7
- **状态：** completed
- **时间：** 2026-03-12T14:00:00

### 输入

需求描述：为 Backlog Manager TUI 应用添加一个查看使用帮助的命令，按 `?` 键后弹出模态窗口，用英文介绍产品的使用方法

读取来源：
- `project-manager.log.md`（PM-7-2）：确认版本 v0.2.0 所有阶段完成，148 个全量测试通过，功能验证 3/3 通过，可正式发布
- `src/app.py`：HelpScreen 实现、`?` 快捷键绑定

### 输出

---

## 验收执行摘要

| 验收项 | 验收方式 | 结论 |
|--------|----------|------|
| HelpScreen 类存在 | 阅读 `app.py` 第 384 行 | 通过 |
| 帮助内容为英文 | 阅读 `HelpScreen.compose()` 内容 | 通过 |
| 帮助内容覆盖所有功能 | 逐项比对快捷键清单 | 通过 |
| `?` 快捷键已绑定 | 检查 `BacklogApp.BINDINGS` | 通过 |
| Esc / q 可关闭帮助窗口 | 检查 `HelpScreen.BINDINGS` | 通过 |
| 帮助文本与实际功能描述一致 | 对比代码实现与帮助文本 | 通过 |

---

## 验收项逐一说明

### 1. HelpScreen 类存在且内容为英文

`src/app.py` 第 384 行：`class HelpScreen(ModalScreen[None])` 类已实现。`compose()` 方法中所有 `Label` 文本均为英文，例如：
- "Backlog Manager — Keyboard Shortcuts"
- "Navigation", "Item Management", "Filters", "Trash", "Other"
- 各快捷键说明均使用英文描述

**结论：满足。**

---

### 2. 帮助内容覆盖所有功能

逐项检查 `HelpScreen.compose()` 中的内容与 `BacklogApp` 实际功能对照：

| 功能 | 快捷键 | 帮助文本中是否覆盖 |
|------|--------|--------------------|
| 导航 | ↑ / ↓ | 是："Move cursor between items" |
| 新增 | a | 是："Add a new item" |
| 编辑 | e | 是："Edit selected item" |
| 删除（移入回收站） | d | 是："Delete selected item (moves to Trash)" |
| 状态切换 | s | 是："Toggle status: Todo → In Progress → Done → In Progress" |
| 搜索/过滤 | / | 是："Open search / filter by keyword" |
| 回收站 | t | 是："Open Trash bin" |
| 恢复（在回收站内） | r (in Trash) | 是："Restore selected item" |
| 永久删除（在回收站内） | x (in Trash) | 是："Permanently delete selected item" |
| 帮助 | ? | 是："Show this help" |
| 退出 | q | 是："Quit" |

所有 11 项功能均已覆盖，包括导航键和所有快捷键。

**结论：满足。**

---

### 3. `?` 快捷键已绑定

`src/app.py` 第 477 行，`BacklogApp.BINDINGS` 中：`Binding("question_mark", "help", "Help")`

第 682-683 行定义了对应的 action 方法：`action_help()` 调用 `self.push_screen(HelpScreen())`

底部状态栏将显示 `? Help` 快捷键提示（`show` 未设为 `False`）。

**结论：满足。**

---

### 4. 按 Esc 或 q 可关闭帮助窗口

`src/app.py` 第 404-407 行，`HelpScreen.BINDINGS` 中：
- `Binding("escape", "dismiss_help", "Close")`
- `Binding("q", "dismiss_help", "Close", show=False)`

两个快捷键均指向 `action_dismiss_help()` 方法，该方法调用 `self.dismiss(None)` 关闭模态窗口。`q` 绑定设置 `show=False`，仅在 `HelpScreen` 层级生效，不会与主界面 `q`（Quit）冲突。

帮助窗口底部也有提示文本："Press [Esc] or [Q] to close"，用户可直观了解关闭方式。

**结论：满足。**

---

### 5. 帮助文本准确性验证

| 帮助文本 | 实际实现 | 准确性 |
|---------|---------|-------|
| `d` → "Delete selected item (moves to Trash)" | `action_delete_item()` 软删除，弹出确认弹窗后移入回收站 | 准确 |
| `s` → "Toggle status: Todo → In Progress → Done → In Progress" | `NEXT_STATUS` 字典：TODO→IN_PROGRESS→DONE→IN_PROGRESS | 准确 |
| `t` → "Open Trash bin" | `action_open_trash()` 调用 `TrashScreen` | 准确 |
| `r (in Trash)` → "Restore selected item" | `TrashScreen.action_restore_item()` 调用 `repo.restore()` | 准确 |
| `x (in Trash)` → "Permanently delete selected item" | `TrashScreen.action_hard_delete_item()` 调用 `repo.hard_delete()`，并再次弹出确认弹窗 | 准确 |
| `?` → "Show this help" | `action_help()` 调用 `push_screen(HelpScreen())` | 准确 |

所有帮助文本内容与实际功能实现一致，无误导性描述。

**结论：满足。**

---

## 已知限制（不影响验收结论）

1. HelpScreen 无 Textual 自动化测试，仅通过源码审查和静态验证（`HelpScreen` 可导入、绑定存在、action 方法存在）
2. 帮助文本硬编码在 `compose()` 中，未来快捷键增减需同步维护，存在内容过时的潜在风险
3. P2 遗留建议（CR-5-3）：`q` 绑定缺少注释说明、分隔符使用硬编码 Unicode 字符而非 `Rule()` widget，不影响功能

---

## 验收结论

**通过**

v0.2.0"查看使用帮助"功能需求完整实现：
- 按 `?` 键弹出英文帮助模态窗口，内容覆盖全部 11 项功能（导航、Add、Edit、Delete、Status、Search、Trash、Restore、Delete Forever、Help、Quit）
- 按 `Esc` 或 `q` 可正确关闭帮助窗口，且 `q` 不会误触发主界面退出
- 帮助文本内容与实际功能实现完全一致，无误导性描述
- 全量回归测试 148/148 通过，新功能不破坏任何现有功能

---
