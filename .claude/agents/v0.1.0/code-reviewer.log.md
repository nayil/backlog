## [CR-5-1] 审查：删除二次确认 + 回收站功能

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-12T00:00:00
- **关联 Developer 条目：** DEV-4-1（developer-core.log.md）、DEV-4-2（developer-ui.log.md）

### 输入

读取 `developer-core.log.md`（DEV-4-1）和 `developer-ui.log.md`（DEV-4-2），并直接审查以下源文件：
- `src/models.py`
- `src/repository.py`
- `src/app.py`

### 输出

---

#### P0 问题（必须修复：功能错误、安全漏洞）

**[P0-1] `ConfirmDeleteScreen` 标题文案与永久删除场景不符**

- **文件：** `src/app.py:249`
- **问题：** `compose()` 中 `Label` 固定写死 `"[bold]Move to Trash?[/bold]"`，但 `TrashScreen` 的 `action_hard_delete_item()` 也复用了同一个 `ConfirmDeleteScreen` 来做永久删除二次确认（见 `app.py:368`）。用户在回收站界面按 `x` 时，弹出的对话框会显示"Move to Trash?"，同时正文还提示"可在 180 天内恢复"，与实际操作（永久删除，不可恢复）完全相反，属于严重误导性文案。
- **建议：** 为 `ConfirmDeleteScreen.__init__` 增加 `mode: str = "trash"` 或 `permanent: bool = False` 参数，根据模式渲染不同标题（"Move to Trash?" vs "Delete Forever?"）和正文（"can be restored within 180 days" vs "This action cannot be undone."）。或者拆分为两个独立的 Screen 类。

---

#### P1 问题（应该修复：性能问题、潜在 Bug）

**[P1-1] `_purge_expired()` 在 `__init__` 中同步执行，阻塞启动**

- **文件：** `src/repository.py:21`
- **问题：** 每次创建 `BacklogRepository` 实例（即每次启动应用）都会执行一次全表 `DELETE`，当回收站数据量大时会增加启动延迟。
- **建议：** 可接受，但若将来数据量增大，建议改为后台线程执行或降低触发频率（如每天一次，通过记录 last_purge 时间戳控制）。当前规模下属于 P1 而非 P0。

**[P1-2] `action_delete_item()` 中 `repo.delete()` 返回值被丢弃**

- **文件：** `src/app.py:571`
- **问题：** `self.repo.delete(item_id)` 返回 `bool` 表示是否成功，但调用方忽略了返回值。若软删除因竞争或其他原因失败（`rowcount == 0`），界面仍会刷新并通知"Item moved to trash"，产生虚假反馈。
- **建议：**
  ```python
  success = self.repo.delete(item_id)
  self._refresh_table()
  if success:
      self.notify("Item moved to trash")
  else:
      self.notify("Delete failed", severity="error")
  ```

**[P1-3] `list_trash()` 包含已过期（expired）条目**

- **文件：** `src/repository.py:194`
- **问题：** `list_trash()` 查询条件是 `deleted_at IS NOT NULL`，没有过滤 `expires_at <= now()`。`_purge_expired()` 只在启动时运行一次，若应用长时间运行，过期条目不会被实时清理，仍会出现在回收站列表中。用户可能尝试恢复一个"应该已过期"的条目（实际上它确实还存在，并不会出错），但这与 180 天保留语义存在轻微不一致。更严重的是，如果将来 `_purge_expired()` 改为后台定期执行，已过期条目就可能实时出现在 UI 中，给用户带来困惑。
- **建议：** `list_trash()` 增加过滤：`WHERE deleted_at IS NOT NULL AND (expires_at IS NULL OR expires_at > ?)` 并传入当前时间；或在 `_refresh_trash()` 之前调用一次 `_purge_expired()`。

**[P1-4] `_migrate_schema()` 对 `ALTER TABLE` 后未 `commit` 隔离**

- **文件：** `src/repository.py:53–55`
- **问题：** 循环中每个 `ALTER TABLE` 执行后没有立即 commit，而是等所有列添加完再统一 commit（第 56 行）。若两列中第一列添加成功但第二列 DDL 失败，`commit` 不会被执行，连接关闭时回滚两列——实际上这是正确行为，但对于 SQLite 而言 DDL 语句本身不在隐式事务内，行为依赖于连接的 `isolation_level` 设置。当 `isolation_level=None`（autocommit）时，`ALTER TABLE` 会立即生效且无法回滚，使 commit 调用无意义。当前代码使用默认 `isolation_level`，行为正确，但依赖了隐式假设，建议加注释说明。
- **建议：** 加注释：`# SQLite DDL statements are auto-committed in some isolation modes; this explicit commit covers the default deferred mode.`

---

#### P2 问题（建议改进：代码风格、可读性）

**[P2-1] `TrashScreen.action_dismiss_screen` 命名与 Textual 约定冲突风险**

- **文件：** `src/app.py:370`
- **问题：** `action_dismiss_screen` 是自定义 action 名，而 `ModalScreen` 本身已有 `dismiss()` 方法。命名上容易与框架内部方法混淆。
- **建议：** 改为 `action_close` 或 `action_close_trash`，与 `BINDINGS` 中的 `"escape"` 绑定名保持对应。

**[P2-2] `_row_to_item()` 检查 `"deleted_at" in keys` 在 `_migrate_schema()` 后永远为真**

- **文件：** `src/repository.py:69–70`
- **问题：** 启动时 `_migrate_schema()` 已确保列存在，因此 `"deleted_at" in keys` 的检查在运行时永远为真，成为死代码。该检查的价值仅在极端情况下（直接构造 `Row` 对象或测试 mock）才体现。
- **建议：** 保留 `row["deleted_at"]` 的 None 判断，去掉 `"deleted_at" in keys` 的 in-check，简化为：
  ```python
  deleted_at=datetime.fromisoformat(row["deleted_at"]) if row["deleted_at"] else None,
  ```
  或保留现有写法并加注释说明防御性检查的意图。

**[P2-3] `BacklogItem.__post_init__` 不设置 `deleted_at`/`expires_at` 的默认时间**

- **文件：** `src/models.py:36–41`
- **问题：** 新字段 `deleted_at`/`expires_at` 不在 `__post_init__` 中初始化（正确——它们默认为 `None`），但 `__post_init__` 中只初始化 `created_at`/`updated_at`，逻辑是一致的，无 bug。仅建议加注释说明 `deleted_at`/`expires_at` 由 repository 层负责设置，而不是 model 层。

**[P2-4] `list_trash()` docstring 描述不准确**

- **文件：** `src/repository.py:193`
- **问题：** docstring 写"Return soft-deleted items that **have not yet expired**"，但实际 SQL 不过滤过期条目（见 P1-3）。文档与实现不符。
- **建议：** 修改 docstring 或修复 SQL（P1-3 的修复会让文档与实现重新对齐）。

---

#### 整体评估

**结论：需修改（有 P0 和 P1 问题）**

整体实现质量较高：
- 向后兼容方案（`_migrate_schema` + `_row_to_item` 防御性读取）设计合理
- 软删除/恢复/永久删除的数据库逻辑正确
- TUI 层 Screen 结构清晰，与现有代码风格一致
- `ConfirmDeleteScreen` 在主界面的使用完全正确

**必须在合并前修复：**
1. **P0-1**：`ConfirmDeleteScreen` 在永久删除场景下显示错误文案，属于功能性误导，用户会看到"Move to Trash?"和"可在 180 天内恢复"的错误提示
2. **P1-2**：`repo.delete()` 返回值被忽略，虚假成功通知

P1-3（`list_trash()` 包含过期条目）建议同步修复，避免未来行为不一致。

---

## [CR-5-2] 第二轮审查：P0/P1 修复验证

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-12T02:00:00
- **关联 Developer 条目：** DEV-5-1（developer-core.log.md）

### 输入

读取 `code-reviewer.log.md`（CR-5-1）上一轮审查报告，以及 `developer-core.log.md`（DEV-5-1）修复记录，并直接核对源文件：
- `src/app.py`
- `src/repository.py`

### 输出

---

#### 逐项验证结论

**[P0-1] ConfirmDeleteScreen 文案在永久删除场景下误导用户**

- **状态：已正确修复**
- **验证：**
  - `app.py:243-246`：`__init__` 新增 `permanent: bool = False` 参数，`self.permanent` 存储。
  - `app.py:249-254`：`compose()` 根据 `self.permanent` 分支渲染：
    - `permanent=True` → 标题 `"[bold]Delete Forever?[/bold]"`，说明 `"This action cannot be undone."`
    - `permanent=False` → 标题 `"[bold]Move to Trash?[/bold]"`，说明 `"...can be restored within 180 days."`
  - `app.py:375`：`TrashScreen.action_hard_delete_item()` 调用 `ConfirmDeleteScreen(title, permanent=True)`，与永久删除语义完全一致。
  - 主界面 `action_delete_item()`（`app.py:585`）调用 `ConfirmDeleteScreen(item.title)` 不传 `permanent`，默认 `False`，保持原有软删除语义。
- **无新问题引入。**

---

**[P1-2] action_delete_item() 丢弃 repo.delete() 返回值**

- **状态：已正确修复**
- **验证：**
  - `app.py:578-583`：
    ```python
    success = self.repo.delete(item_id)
    self._refresh_table()
    if success:
        self.notify("Item moved to trash")
    else:
        self.notify("Delete failed", severity="error")
    ```
  - 返回值被捕获，成功/失败路径分别给出不同通知，与 CR-5-1 建议完全一致。
- **无新问题引入。**

---

**[P1-3] list_trash() 包含已过期条目**

- **状态：已正确修复**
- **验证：**
  - `repository.py:192-199`：
    - docstring 更新为 `"Return soft-deleted items that have not yet expired, newest first."`（与实现一致）
    - SQL：`WHERE deleted_at IS NOT NULL AND (expires_at IS NULL OR expires_at > ?) ORDER BY deleted_at DESC`，传入 `datetime.now().isoformat()`
  - 过滤逻辑正确：`expires_at IS NULL` 保留永不过期条目，`expires_at > ?` 过滤已过期条目。
- **无新问题引入。**

---

#### 修复引入的新问题检查

扫描修复涉及的所有改动，未发现新引入的 P0/P1 问题：

- `ConfirmDeleteScreen.__init__` 使用 `permanent: bool = False` 默认参数，不影响任何已有调用方。
- `action_delete_item()` 的修复仅增加了返回值检查，逻辑与原来等价（原来总是刷新并通知成功），新逻辑在 `success=False` 时给出更准确的错误通知，行为更正确。
- `list_trash()` SQL 新增 `expires_at` 过滤，语义收窄（排除过期条目），与 `_purge_expired()` 的清理逻辑一致，不会导致"可恢复条目被错误过滤"的问题（`expires_at IS NULL` 保护了不设过期时间的条目）。

上一轮遗留的 P1-1（`_purge_expired` 同步执行）和 P1-4（`_migrate_schema` 注释）本轮未做修复，符合预期（CR-5-1 中 P1-1 已标注为可接受，P1-4 为注释建议）。

---

#### 整体评估

**结论：通过（无 P0/P1 问题）**

全部 P0 和 P1 问题均已在 DEV-5-1 中正确修复，修复实现与 CR-5-1 的建议方案一致，未引入新的回归问题。代码可以进入阶段 6（测试验证）。

剩余 P2 问题（P2-1 至 P2-4）可在后续迭代中处理，不阻塞当前合并。

---

## [CR-5-3] 第三轮审查：HelpScreen + `?` 快捷键（DEV-4-3）

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-12T12:00:00
- **关联 Developer 条目：** DEV-4-3（developer-ui.log.md）

### 输入

读取 `developer-ui.log.md`（DEV-4-3）中 HelpScreen 实现描述，并直接核对 `src/app.py`（第 381–683 行）。

### 输出

---

#### P0 问题（必须修复：功能错误、安全漏洞）

**无 P0 问题。**

---

#### P1 问题（应该修复：性能问题、潜在 Bug）

**无 P1 问题。**

---

#### P2 问题（建议改进：代码风格、可读性）

**[P2-5] HelpScreen 中 `q` 绑定的 `show=False` 依赖行为未注释说明**

- **文件：** `src/app.py:406`
- **问题：** `Binding("q", "dismiss_help", "Close", show=False)` 利用 `show=False` 使 `q` 不出现在 Footer，同时将其作用域限制在 ModalScreen 层，防止穿透到 BacklogApp 的 `action_quit`。这是正确的 Textual 用法，但对于不熟悉框架 Binding 优先级机制的维护者来说，这段代码可能引发困惑（为什么 `q` 不直接调用 Quit？）。
- **建议：** 添加行内注释：`# show=False: hide from Footer; scope limited to this ModalScreen, won't propagate to app-level quit`

**[P2-6] HelpScreen `compose()` 使用硬编码分隔符字符串而非 Widget**

- **文件：** `src/app.py:412, 434`
- **问题：** `yield Label("─" * 43)` 用硬编码 Unicode box-drawing 字符和固定宽度模拟分隔线。当容器宽度变化或字体渲染不对齐时，分隔线长度可能与内容宽度不匹配。
- **建议：** 可接受（当前固定宽度 60 的容器不会动态变化），但可改用 `Rule()` widget（Textual 内置分隔线）以获得更好的自适应性。属于低优先级改进。

**[P2-7] HelpScreen 快捷键文档中 `s` 状态循环描述不完整**

- **文件：** `src/app.py:420`
- **问题：** Help 文档写 `"Toggle status: Todo → In Progress → Done → In Progress"`，但实际 `NEXT_STATUS` 字典（`app.py:47–51`）对 `DONE` 的后继是 `IN_PROGRESS`，而 `IN_PROGRESS` 的后继是 `DONE`，即循环路径为 `Todo → In Progress ↔ Done`（从 `Todo` 出发只能到 `In Progress`，不能直接循环回 `Todo`）。文档中的循环箭头表述容易误导用户认为可以从 `Done` 再回到 `Todo`，实际上需要先 `Done → In Progress → Todo` 是不可能的（`transition_status` 不允许 `TODO → DONE` 直接跳跃，但 `IN_PROGRESS → TODO` 是允许的，而 `NEXT_STATUS` 中 `IN_PROGRESS` 映射到 `DONE`，不是 `TODO`）。
  - 实际用户体验：按 `s` 只能推进 `Todo → In Progress → Done`，之后再按 `s` 会回到 `In Progress`（`Done → In Progress`），无法再回 `Todo`（因为 `NEXT_STATUS[IN_PROGRESS] = DONE`）。
  - 文档应更准确地描述为：`"Advance status: Todo → In Progress → Done → In Progress (cycle)"`。
- **建议：** 修改 `app.py:420` 的 Label 文本为 `"   s              Advance status: Todo → In Progress → Done → …"` 或类似更准确的描述。

---

#### 整体评估

**结论：通过（无 P0/P1 问题）**

HelpScreen 实现质量良好：
- 与现有 ModalScreen 模式（`ItemFormScreen`、`SearchScreen`、`TrashScreen`）风格一致
- `q` 绑定作用域设计正确，不影响主界面 Quit 功能
- 快捷键覆盖完整，涵盖所有已实现功能
- 无新增 import，依赖最小化

DEV-4-3 可进入阶段 6（测试验证）。P2 问题（P2-5 至 P2-7）可在后续迭代中酌情处理。

---
