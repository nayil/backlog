## [DEV-4-2] TUI 层实现：ConfirmDeleteScreen + TrashScreen + BacklogApp 变更

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-12T00:00:00

### 输入

读取 `tech-leader.log.md`（TL-2-1）中的模块 3 规格，以及 `developer-core.log.md`（DEV-4-1）中数据层的接口产出，实现 TUI 层全部改动。

### 输出

#### 改动说明

**目标：** 在 `src/app.py` 中新增删除确认对话框和回收站视图，并串联到主界面。

**改动文件：** `src/app.py`

## [DEV-4-3] TUI 层实现：HelpScreen + BacklogApp `?` 快捷键绑定

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-12T10:30:00

### 输入

读取 `tech-leader.log.md`（TL-2-2）中关于"查看使用帮助"功能的技术方案，基于现有 `src/app.py` 的 ModalScreen 模式实现。

### 输出

#### 改动说明

**目标：** 在 `src/app.py` 中新增 `HelpScreen` 模态窗口，并在 `BacklogApp` 中注册 `?` 快捷键。

**改动文件：** `src/app.py`

---

#### 改动详情

##### 1. HelpScreen（新增，位于 TrashScreen 和 BacklogApp 之间）

```python
class HelpScreen(ModalScreen[None]):
    def action_dismiss_help(self) -> None: ...
```

- 继承 `ModalScreen[None]`，与现有 `TrashScreen` 模式一致，无需参数
- 按键绑定：
  - `Escape` → `action_dismiss_help()`：`dismiss(None)`
  - `q` → `action_dismiss_help()`，`show=False`，避免在 Footer 重复显示且不穿透到 App 层的 Quit
- CSS 内联：居中弹窗，宽 60，`max-height: 85%`，`$accent` 边框，参照现有 Screen 风格
- `compose()` 使用 `Vertical(id="help-container")` 包裹多个 `Label`，内容覆盖所有快捷键：
  - Navigation（↑/↓）
  - Item Management（a/e/d/s）
  - Filters（/，顶部下拉框）
  - Trash（t，r/x in Trash）
  - Other（?, q）
- 无新增 import，所有依赖（`ModalScreen`、`Vertical`、`Label`、`Binding`）已存在

##### 2. BacklogApp 变更

| 变更点 | 说明 |
|--------|------|
| `BINDINGS` | 在 `slash` 绑定之后、`q` 绑定之前新增 `Binding("question_mark", "help", "Help")` |
| `action_help()`（新增） | `self.push_screen(HelpScreen())`，无回调（HelpScreen 返回 None，无需刷新界面） |

**向后兼容：**
- `?` 快捷键此前未被占用，无冲突
- `HelpScreen` 中的 `q` 绑定作用域限于 ModalScreen，不影响主界面的 Quit 功能
- 不涉及数据层改动（`models.py`、`repository.py` 均未修改）

---

#### 改动详情

##### 1. ConfirmDeleteScreen（新增，第207–260行）

```python
class ConfirmDeleteScreen(ModalScreen[bool]):
    def __init__(self, item_title: str) -> None
```

- 继承 `ModalScreen[bool]`，与现有 `ItemFormScreen`/`SearchScreen` 模式一致
- 按键绑定：`y`/`Enter` → `dismiss(True)`，`n`/`Esc` → `dismiss(False)`
- UI：红色边框（`$error`）小弹窗，显示条目标题和 180 天保留说明
- Enter 绑定设 `show=False`，避免在 Footer 重复显示

##### 2. TrashScreen（新增，第263–373行）

```python
class TrashScreen(ModalScreen[None]):
    def __init__(self, repo: BacklogRepository) -> None
```

- 继承 `ModalScreen[None]`，接受 `repo` 引用（由 BacklogApp 传入）
- DataTable 列：ID、Title、Category、Deleted At、Expires At
- 按键绑定：
  - `r` → `action_restore_item()`：调用 `repo.restore()`，成功后刷新列表
  - `x` → `action_hard_delete_item()`：先通过 `repo.get(id, include_deleted=True)` 获取标题，再 push `ConfirmDeleteScreen` 二次确认，确认后调用 `repo.hard_delete()`
  - `Esc` → `action_dismiss_screen()`：`dismiss(None)`
- 内部辅助方法 `_selected_item_id()` 与主界面保持相同写法
- 永久删除复用 `ConfirmDeleteScreen`，通过 `self.app.push_screen()` 推送

##### 3. BacklogApp 变更

| 变更点 | 说明 |
|--------|------|
| `BINDINGS` | 新增 `Binding("t", "open_trash", "Trash")` |
| `action_delete_item()` | 先 `repo.get(item_id)` 获取标题，再 push `ConfirmDeleteScreen`；确认后调用 `repo.delete()`（软删除），通知文字改为 "Item moved to trash" |
| `action_open_trash()`（新增） | push `TrashScreen(self.repo)`，关闭回调中调用 `_refresh_table()`，确保恢复/永久删除后主界面同步更新 |

**向后兼容：**
- `_refresh_table()` 无需改动（`repo.list()` 已过滤软删除条目，由 developer-core 保证）
- 所有新 Screen 均为独立类，不影响现有 `ItemFormScreen`/`SearchScreen`

---
