## [TL-2-1] 删除二次确认与回收站功能技术方案

- **阶段：** 2
- **状态：** completed
- **时间：** 2026-03-12T00:00:00

### 输入

需求：
1. 删除二次确认：用户按 `d` 时弹出确认对话框，二次确认后才执行删除
2. 回收站功能：软删除，最大保留 180 天，保留期内可恢复

现有架构：
- `src/models.py`：BacklogItem dataclass，Status/Priority 枚举
- `src/repository.py`：BacklogRepository（SQLite），`delete()` 直接 DELETE FROM
- `src/app.py`：BacklogApp（Textual TUI），`action_delete_item()` 直接调用 `repo.delete()` 无确认

### 输出

---

## 技术方案概述

本次改动分为两个独立但协作的功能模块：

### 功能 A：删除二次确认

在 TUI 层新增一个 `ConfirmDeleteScreen` 模态框（参照现有 `ItemFormScreen`/`SearchScreen` 的 `ModalScreen` 模式），由 `action_delete_item()` 在执行删除前先 push 该 Screen，用户确认后再执行软删除。

### 功能 B：回收站（软删除）

**数据库层**：在 `backlog_items` 表新增两列：
- `deleted_at TEXT DEFAULT NULL`：软删除时间戳，NULL 表示正常条目
- `expires_at TEXT DEFAULT NULL`：过期时间（`deleted_at + 180天`），供清理查询使用

所有现有查询过滤 `deleted_at IS NULL`（正常列表），被软删除的条目 `deleted_at IS NOT NULL`。

**应用层**：新增回收站视图入口（快捷键 `R`），展示 `deleted_at IS NOT NULL` 的条目；在回收站视图中可按 `r` 恢复、按 `x` 永久删除。

**清理策略**：在 `BacklogRepository.__init__` 中调用 `_purge_expired()`，清除 `expires_at <= now()` 的条目，轻量、同步、无需后台线程。

---

## 模块划分

### 模块 1：数据模型扩展（`src/models.py`）

**职责：** 扩展 `BacklogItem` dataclass，支持软删除字段。

**接口变更：**
- `BacklogItem` 新增字段：
  - `deleted_at: Optional[datetime] = None`
  - `expires_at: Optional[datetime] = None`
- `to_dict()` / `from_dict()` 同步加入这两个字段
- 无新枚举，无破坏性变更

**依赖：** 无上游依赖，是下游所有模块的基础。

---

### 模块 2：数据库层扩展（`src/repository.py`）

**职责：** 实现软删除、恢复、过期清理，以及回收站查询接口。

**接口变更：**

| 方法 | 变更说明 |
|------|----------|
| `_create_table()` | 新增 `deleted_at`、`expires_at` 列（`ALTER TABLE IF NOT EXISTS` 或 `CREATE TABLE` 时直接加列） |
| `_row_to_item()` | 解析新列 |
| `list(...)` | 默认过滤 `deleted_at IS NULL` |
| `get(item_id)` | 默认只查非删除条目；新增 `include_deleted=False` 参数 |
| `delete(item_id)` | 改为软删除：`UPDATE SET deleted_at=now, expires_at=now+180d WHERE id=?` |
| `restore(item_id) -> Optional[BacklogItem]` | **新增**：`UPDATE SET deleted_at=NULL, expires_at=NULL WHERE id=?` |
| `hard_delete(item_id) -> bool` | **新增**：`DELETE FROM`（仅供回收站永久删除使用） |
| `list_trash(...) -> List[BacklogItem]` | **新增**：查询 `deleted_at IS NOT NULL ORDER BY deleted_at DESC` |
| `_purge_expired()` | **新增**：`DELETE FROM WHERE expires_at <= now()`，在 `__init__` 中调用 |

**Schema 迁移策略：**
在 `_create_table()` 之后，调用 `_migrate_schema()` 私有方法，使用 `ALTER TABLE backlog_items ADD COLUMN deleted_at TEXT DEFAULT NULL` 加列（`IF NOT EXISTS` 不支持 SQLite，改用 `PRAGMA table_info` 检查列是否已存在，不存在则执行 ALTER）。

**依赖：** 依赖模块 1（BacklogItem 字段扩展）。

---

### 模块 3：TUI 层（`src/app.py`）

#### 子模块 3a：ConfirmDeleteScreen

**职责：** 新增删除二次确认的模态对话框。

**接口：**
```
class ConfirmDeleteScreen(ModalScreen[bool]):
    def __init__(self, item_title: str) -> None
    # 返回 True（确认删除）或 False（取消）
    BINDINGS: [("y", "confirm", "Yes"), ("n"/"escape", "cancel", "No")]
```

- UI 样式：小型居中弹窗，显示条目标题和确认提示文字
- 与现有 `ItemFormScreen`、`SearchScreen` 同级，CSS 内联

#### 子模块 3b：TrashScreen

**职责：** 回收站独立模态视图，展示已软删除条目，支持恢复和永久删除。

**接口：**
```
class TrashScreen(ModalScreen[None]):
    # 展示 repo.list_trash() 结果
    # 内部持有 repo 引用（由 BacklogApp 传入构造函数）
    BINDINGS: [
        ("r", "restore_item", "Restore"),
        ("x", "hard_delete_item", "Delete Forever"),
        ("escape", "dismiss", "Close"),
    ]
```

- 展示列：ID、Title、Category、DeletedAt、ExpiresAt
- 恢复后关闭并通知主界面刷新
- 永久删除需再次调用 `ConfirmDeleteScreen` 做二次确认

#### 子模块 3c：BacklogApp 变更

**职责：** 串联新功能到现有流程。

**变更点：**

| 变更 | 说明 |
|------|------|
| `action_delete_item()` | push `ConfirmDeleteScreen`，回调中执行 `repo.delete()`（现在是软删除） |
| 新增 `action_open_trash()` | push `TrashScreen`，关闭后调用 `_refresh_table()` |
| BINDINGS 新增 | `("r", "open_trash", "Trash")` 或 `("shift+r"/"R")` 映射到打开回收站 |
| `_refresh_table()` | 无需改动（`repo.list()` 已过滤软删除条目） |

**依赖：** 依赖模块 2 的新接口（`restore`、`hard_delete`、`list_trash`）。

---

### 模块 4：迁移兼容性（`src/migration.py`）

**职责：** 确保 JSON→SQLite 迁移工具在新 schema 下正常工作。

**变更：** 迁移时将 `deleted_at` 和 `expires_at` 默认填 `NULL`（即所有迁移条目均为正常状态）。

**依赖：** 依赖模块 1、模块 2。

---

## 开发计划

### 开发顺序（有依赖关系，串行）

```
模块 1（models.py）
    ↓
模块 2（repository.py）
    ↓
模块 3（app.py：ConfirmDeleteScreen + TrashScreen + App 变更）
    ↓
模块 4（migration.py 兼容性确认）
```

### 并行策略

- 模块 3a（ConfirmDeleteScreen）和 模块 3b（TrashScreen）在模块 2 完成后可由不同 Developer 并行实现，因为两者在 app.py 中相互独立，最终由模块 3c 串联。
- 模块 4（migration.py）改动量极小，可与模块 3 并行进行。

### 推荐 Developer 分工

| Developer | 负责模块 | 日志文件 |
|-----------|----------|----------|
| Developer-core | 模块 1 + 模块 2（数据层）| `developer-core.log.md` |
| Developer-ui | 模块 3（TUI 层全部）+ 模块 4 | `developer-ui.log.md` |

如需进一步拆分，可将 3a/3b/3c 各自独立，但 app.py 存在编辑冲突风险，建议由单一 Developer 串行完成 TUI 部分。

---

## 技术风险与应对

| 风险 | 等级 | 应对方案 |
|------|------|----------|
| SQLite 不支持 `ALTER TABLE ADD COLUMN IF NOT EXISTS` | 中 | 用 `PRAGMA table_info(backlog_items)` 检查列存在性，不存在再执行 `ALTER TABLE` |
| 现有测试/代码直接断言 DELETE 行为 | 低 | `delete()` 改为软删除后，现有调用方行为不变（返回 bool），但语义变化；需通知 CodeReviewer 重点关注 |
| TrashScreen 中恢复/永久删除后主界面未刷新 | 低 | `TrashScreen` dismiss 时主 App 在 callback 中调用 `_refresh_table()` |
| 回收站条目 `expires_at` 计算精度 | 低 | 使用 Python `datetime.now() + timedelta(days=180)`，存为 ISO 字符串，无时区问题（与现有字段一致） |
| 180 天清理在数据库层做，无后台调度 | 低-中 | 启动时同步清理，开销极小（一条 DELETE SQL），满足需求；若未来条目量极大再考虑异步 |
| Textual 版本兼容性（`ModalScreen` 泛型参数） | 低 | 参照现有 `ItemFormScreen[Optional[BacklogItem]]` 写法保持一致 |

---

## 接口约定汇总（供 Developer 参考）

### repository.py 新增/变更方法签名

```python
# 软删除（原 delete 语义不变，但改为 UPDATE）
def delete(self, item_id: int) -> bool: ...

# 从回收站恢复
def restore(self, item_id: int) -> Optional[BacklogItem]: ...

# 永久删除（仅限回收站中的条目）
def hard_delete(self, item_id: int) -> bool: ...

# 查询回收站
def list_trash(self) -> List[BacklogItem]: ...

# 内部：清理过期条目（在 __init__ 中调用）
def _purge_expired(self) -> None: ...

# 内部：按需迁移 schema
def _migrate_schema(self) -> None: ...
```

### app.py 新增 Screen 签名

```python
class ConfirmDeleteScreen(ModalScreen[bool]):
    def __init__(self, item_title: str) -> None: ...

class TrashScreen(ModalScreen[None]):
    def __init__(self, repo: BacklogRepository) -> None: ...
```

---

- **关联需求：** 删除二次确认 + 回收站（180 天保留 + 恢复）
- **预估复杂度：** 中等（主要在 TUI 层新增两个 Screen，数据层改动清晰）
- **后续建议：** 可考虑在回收站视图增加"一键清空"功能，但不在本次需求范围内

---

## [TL-9-1] v0.1.0 技术总结报告

- **阶段：** 9（阶段 7 - 项目总结）
- **状态：** completed
- **时间：** 2026-03-12T05:00:00

### 输入

读取 v0.1.0 目录下全部日志文件：
- `tech-leader.log.md`（TL-2-1）：技术方案，状态 completed
- `project-manager.log.md`（PM-2-1、PM-3-1、PM-7-1）：项目计划、对齐评估、发布确认，状态 completed
- `developer-core.log.md`（DEV-4-1、DEV-5-1）：数据层实现 + P0/P1 修复，状态 completed
- `developer-ui.log.md`（DEV-4-2）：TUI 层实现，状态 completed
- `code-reviewer.log.md`（CR-5-1、CR-5-2）：两轮代码审查，状态 completed
- `tester.log.md`（TST-6-1）：42 个新增测试，148 个总测试全部通过，状态 completed
- `customer.log.md`（CUST-7-1）：客户验收，8 项全部通过，状态 completed

### 输出

---

## 技术总结报告：v0.1.0 删除二次确认与回收站功能

### 一、架构决策回顾

#### 决策 1：软删除在原表新增列，而非独立 trash 表

**决策内容：** 在 `backlog_items` 表新增 `deleted_at TEXT DEFAULT NULL` 和 `expires_at TEXT DEFAULT NULL` 两列，而非创建独立的 `trash_items` 表。

**决策背景：** 阶段 2（TL-2-1）提出这一设计；PM-3-1 对齐时 PM 提出了同样的疑问，TL 确认采用原表加列方案。

**决策理由：**
- 恢复操作仅需 UPDATE 而非跨表数据迁移，实现简洁
- 保留条目 ID 连续性，避免主/回收站 ID 冲突
- 主界面查询过滤 `deleted_at IS NULL` 即可，对现有代码改动最小
- 历史查询（按 ID 关联）无需 JOIN，数据完整性更好

**实际验证：** 该决策使 Developer-core 实现时改动范围清晰可控，代码审查未发现该设计层面的 P0/P1 问题，客户验收中 8 项功能脚本全部一次通过。

---

#### 决策 2：引入 `expires_at` 显式存储过期时间

**决策内容：** 除 `deleted_at` 外，额外引入 `expires_at = deleted_at + 180天` 存入数据库，而非每次查询动态计算。

**决策背景：** PM-2-1 原方案仅用 `deleted_at + 180天` 动态计算过期，TL-2-1 改为显式存储 `expires_at`，PM-3-1 复核时评为"优点明显、建议保留"。

**决策理由：**
- `_purge_expired()` 的清理 SQL 可直接使用 `WHERE expires_at <= now()`，无需日期计算，性能更好
- 回收站列表过滤同样受益（P1-3 修复后 `list_trash()` 使用了 `expires_at > now()` 过滤）
- 支持未来灵活调整单个条目的保留期，而无需修改全局策略
- `TrashScreen` 中可直接展示 `expires_at` 列，用户体验更直观

**实际验证：** P1-3 的修复（`list_trash()` 增加过期过滤）直接利用了 `expires_at` 字段，若只有 `deleted_at` 则该修复的 SQL 会更复杂。

---

#### 决策 3：`_purge_expired()` 在 Repository `__init__` 中同步执行，而非在 TUI `on_mount` 中

**决策背景：** PM-2-1 建议在 `app.py` 的 `on_mount` 中调用清理逻辑；TL-2-1 将其放在 `BacklogRepository.__init__` 中；PM-3-1 对齐时 PM 接受 TL 方案，认为"Repository 层自管理，测试更独立"。

**决策理由：**
- Repository 层不依赖 TUI 生命周期，可独立实例化和测试
- 清理逻辑对 TUI 层不可见，分层边界清晰
- 单元测试（TST-6-1 中 `test_purge_expired_removes_past_expires`）可直接测试 Repository，无需启动 TUI

**实际验证：** Tester 在 TST-6-1 中对 `_purge_expired()` 编写了独立的单元测试，确实验证了"Repository 自管理"设计的可测试性优势。

---

#### 决策 4：`ConfirmDeleteScreen` 复用于软删除和永久删除，通过 `permanent` 参数区分

**决策背景：** TL-2-1 原设计中 `TrashScreen` 永久删除时复用同一个 `ConfirmDeleteScreen`。CR-5-1 发现 P0-1（复用同一 Screen 但文案未区分），DEV-5-1 通过新增 `permanent: bool = False` 参数修复，CR-5-2 验证修复正确。

**最终决策：** 保持 Screen 复用，新增参数区分两种模式，而非拆分为两个独立 Screen 类。

**决策理由：**
- 两种确认逻辑（布局、按键绑定）完全相同，仅文案不同，无需重复代码
- `permanent` 参数默认为 `False`，不影响任何已有调用方，向后兼容
- 减少 `app.py` 中的 Screen 类数量，降低后续维护成本

**实际教训：** 该问题本可在 TL-2-1 技术方案阶段提前识别（复用 Screen 时需预判文案差异），未来类似设计应在接口约定中明确区分参数。

---

#### 决策 5：`app.py` TUI 层由单一 Developer-ui 串行完成，不拆分并行

**决策背景：** TL-2-1 中提出 3a/3b/3c 可拆分为多 Developer 并行，但同时指出"app.py 存在编辑冲突风险"，建议串行。PM-3-1 复核确认，采用串行策略。

**决策理由：**
- `ConfirmDeleteScreen`、`TrashScreen`、`BacklogApp` 变更三者均在同一文件 `app.py`，并行开发存在合并冲突风险
- 串行实现反而因为 Developer-ui 可以掌握全文件上下文，使最终集成更顺畅（DEV-4-2 产出一次通过 CR-5-1 的 TUI 层部分）

---

### 二、技术债务清单

以下问题经代码审查（CR-5-1、CR-5-2）识别，P2 级别，不影响功能，在 v0.1.0 中未处理，记录为技术债务：

#### TD-1：`TrashScreen.action_dismiss_screen` 命名与 Textual 约定冲突风险（P2-1）

- **文件：** `src/app.py`
- **问题：** 自定义 action 名 `action_dismiss_screen` 与 `ModalScreen` 内置 `dismiss()` 方法命名相近，易造成混淆
- **建议改法：** 重命名为 `action_close` 或 `action_close_trash`
- **影响：** 仅代码可读性，无运行时 Bug

#### TD-2：`_row_to_item()` 中 `"deleted_at" in keys` 检查在运行时为死代码（P2-2）

- **文件：** `src/repository.py`
- **问题：** `_migrate_schema()` 已保证列存在，`in keys` 检查在实际运行路径下永远为真
- **建议改法：** 简化为 `datetime.fromisoformat(row["deleted_at"]) if row["deleted_at"] else None`，或保留并加防御性注释
- **影响：** 代码简洁性，有无均不影响功能

#### TD-3：`BacklogItem` 中 `deleted_at`/`expires_at` 缺少注释说明（P2-3）

- **文件：** `src/models.py`
- **问题：** `__post_init__` 中未注释说明 `deleted_at`/`expires_at` 由 Repository 层负责设置而非 Model 层
- **建议改法：** 在字段定义处加 docstring 或注释，明确职责边界
- **影响：** 代码可读性

#### TD-4：TUI 层无自动化测试（客户验收已知限制）

- **涉及：** `src/app.py` 中 `ConfirmDeleteScreen` 和 `TrashScreen`
- **问题：** Textual UI 自动化测试（`App.run_test()`）未在 v0.1.0 中实现，仅通过源码审查和手动验收覆盖
- **影响：** 未来 TUI 改动缺乏自动化回归保障，需依赖手动测试
- **建议：** 补充 Textual 测试套件，覆盖弹窗触发/取消、回收站恢复/永久删除流程

#### TD-5：`_purge_expired()` 无频率限制，每次 Repository 初始化均执行（P1-1，已接受）

- **文件：** `src/repository.py`
- **问题：** 启动时同步全表 DELETE，当回收站数据量极大时可能轻微增加启动延迟
- **当前影响：** 当前数据规模下可忽略
- **建议改法（未来）：** 记录 `last_purge` 时间戳，改为每天最多触发一次；或改为后台线程异步执行

#### TD-6：`deleted_at`/`expires_at` 使用 naive datetime，不含时区信息（已知限制）

- **涉及：** `src/models.py`、`src/repository.py`
- **问题：** 与现有 `created_at`/`updated_at` 保持一致（均为本地时间 naive datetime），跨时区场景下 180 天保留期计算可能有轻微偏差
- **当前影响：** 单机本地使用场景下无影响
- **建议改法（未来）：** 若系统需支持多时区，统一改为 UTC 时间存储（`datetime.utcnow()`），并在展示层转换为本地时间

---

### 三、后续建议

#### 短期（下一个迭代可优先考虑）

1. **补充 TUI 层自动化测试**（对应 TD-4）
   - 使用 Textual 的 `App.run_test()` 为 `ConfirmDeleteScreen` 和 `TrashScreen` 编写自动化测试
   - 覆盖场景：按 `y`/`n` 确认取消、回收站恢复后主界面刷新、永久删除二次确认流程

2. **处理 P2 技术债务**（对应 TD-1～TD-3）
   - 重命名 `action_dismiss_screen`、简化 `_row_to_item()` 防御检查、添加字段注释
   - 改动量小，建议集中在一次 chore PR 中处理

3. **回收站"一键清空"功能**
   - 在 `TrashScreen` 中增加 `Shift+X` 或专用按键，一次性永久删除所有回收站条目
   - Repository 层新增 `hard_delete_all_trash()` 方法，内部调用 `DELETE WHERE deleted_at IS NOT NULL`

#### 中期（架构优化）

4. **`_purge_expired()` 改为频率限制触发**（对应 TD-5）
   - 在 Repository 或配置层记录 `last_purge_at`（存入 SQLite 的 `metadata` 表或配置文件）
   - 超过 24 小时未清理才触发，避免每次启动都执行全表 DELETE

5. **回收站数据量优化**
   - 在 `deleted_at` 列建索引（`CREATE INDEX IF NOT EXISTS idx_deleted_at ON backlog_items(deleted_at)`）
   - 当前数据规模下 `list_trash()` 性能无问题，数据量增长后受益明显

#### 长期（架构演进）

6. **时区支持**（对应 TD-6）
   - 若系统演进为多用户/云端场景，统一将时间戳改为 UTC 存储，展示层本地化转换
   - 需要数据迁移脚本，影响范围较大，建议单独立项

7. **回收站保留期可配置化**
   - 当前 180 天硬编码在 Repository 层（`timedelta(days=180)`)
   - 可引入配置项（如 `~/.config/backlog/settings.toml`）允许用户自定义保留天数

---

### 四、开发过程回顾

| 阶段 | 关键事件 | 结论 |
|------|----------|------|
| 阶段 2（技术规划） | TL 引入 `expires_at` 显式字段，超出 PM 原方案 | PM 复核认可，提升了后续实现质量 |
| 阶段 3（计划对齐） | 清理时机（`__init__` vs `on_mount`）存在分歧 | 一轮对齐即达成共识，效率高 |
| 阶段 4（并行开发） | Developer-core 完成数据层后，Developer-ui 独立完成 TUI 层 | 串行策略规避了 app.py 编辑冲突 |
| 阶段 5（代码审查） | CR-5-1 发现 P0-1（文案误导）和 P1-2/P1-3 | 体现了代码审查对语义正确性的把关价值 |
| 阶段 5（P0/P1 修复） | DEV-5-1 一轮修复了全部 P0/P1 | 修复精准，CR-5-2 第二轮直接通过 |
| 阶段 6（测试验证） | 42 新增测试，148 总测试一轮全部通过，无 Tester → Developer 修复循环 | 数据层实现质量高，P1-3 修复已被测试覆盖 |
| 阶段 7（客户验收） | 8 项功能验收脚本全部通过 | 需求完整交付，无遗留 P0/P1 问题 |

**整体评估：** v0.1.0 开发过程顺畅，仅在代码审查阶段发现 1 个 P0 问题需修复（文案误导），主要源于技术方案阶段未充分考虑 Screen 复用场景的文案差异。其余技术决策均在实现中得到正向验证。

---

- **版本：** v0.1.0
- **发布日期：** 2026-03-12
- **总测试数：** 148（全部通过）
- **新增功能：** 删除二次确认、回收站（软删除 + 180 天保留 + 恢复 + 过期清理）
- **改动文件：** `src/models.py`、`src/repository.py`、`src/app.py`、`tests/test_models.py`、`tests/test_repository.py`

---

## [TL-2-2] "查看使用帮助"功能技术方案

- **阶段：** 2
- **状态：** completed
- **时间：** 2026-03-12T10:00:00

### 输入

需求：用户按下 `?` 快捷键后，弹出一个模态窗口，用英文介绍产品的所有功能和使用方法（快捷键列表、功能说明等）

现有架构分析（基于 `src/app.py`）：
- 已存在 `ModalScreen` 模式：`ItemFormScreen`、`SearchScreen`、`ConfirmDeleteScreen`、`TrashScreen`
- `BacklogApp.BINDINGS` 已有 7 个快捷键绑定：`a`（Add）、`e`（Edit）、`d`（Delete）、`s`（Status）、`t`（Trash）、`/`（Search）、`q`（Quit）
- Textual 已 import：`ModalScreen`、`Static`、`Label`、`Vertical`、`Binding`
- `?` 快捷键当前未被占用

### 输出

---

## 技术方案概述

本次改动为**单模块、单文件**的小型功能增量。在 `src/app.py` 中新增一个 `HelpScreen(ModalScreen)` 类，并在 `BacklogApp` 中注册 `?` 快捷键及对应 action。改动范围极小，不涉及数据层（`models.py`、`repository.py`）。

---

## 模块划分

### 模块 1（唯一模块）：HelpScreen + BacklogApp 绑定（`src/app.py`）

#### 子模块 1a：HelpScreen 类

**职责：** 展示帮助信息的只读模态窗口，用户按任意 `Escape` 关闭。

**接口定义：**

```python
class HelpScreen(ModalScreen[None]):
    """Modal screen displaying keyboard shortcuts and feature descriptions."""

    CSS: str  # 内联 CSS，控制居中弹窗样式

    BINDINGS = [
        Binding("escape", "dismiss_help", "Close"),
        Binding("q", "dismiss_help", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        # 渲染帮助内容容器
        ...

    def action_dismiss_help(self) -> None:
        self.dismiss(None)
```

**帮助内容结构（英文）：**

```
Backlog Manager — Keyboard Shortcuts
─────────────────────────────────────────
 Navigation
   ↑ / ↓          Move cursor between items

 Item Management
   a              Add a new item
   e              Edit selected item
   d              Delete selected item (moves to Trash)
   s              Toggle status: Todo → In Progress → Done → In Progress

 Filters
   /              Open search / filter by keyword
   (Status & Category dropdowns at top)

 Trash
   t              Open Trash bin
   r (in Trash)   Restore selected item
   x (in Trash)   Permanently delete selected item

 Other
   ?              Show this help
   q              Quit
─────────────────────────────────────────
Press [Esc] or [Q] to close
```

**CSS 设计（参照现有 Screen 风格）：**

```css
HelpScreen {
    align: center middle;
}
#help-container {
    width: 60;
    height: auto;
    max-height: 85%;
    border: thick $accent;
    background: $surface;
    padding: 1 2;
}
#help-container Label {
    margin-bottom: 1;
}
```

**依赖：** 仅依赖 Textual 已导入组件（`ModalScreen`、`Static`、`Label`、`Vertical`、`Binding`），无新增 import。

---

#### 子模块 1b：BacklogApp 变更

**职责：** 注册 `?` 快捷键，添加 `action_help` 方法。

**变更点：**

| 变更 | 代码位置 | 内容 |
|------|----------|------|
| `BINDINGS` 新增 | `BacklogApp.BINDINGS` 列表 | `Binding("question_mark", "help", "Help")` |
| `action_help` 新增 | `BacklogApp` 方法 | `self.push_screen(HelpScreen())` |

**Textual 快捷键说明：**
- `?` 在 Textual 中的键名为 `"question_mark"`（不是 `"?"`），与现有 `"slash"` 命名约定一致（`/` 对应 `"slash"`）

**依赖：** 依赖子模块 1a（HelpScreen 类）。

---

## 开发计划

### 开发顺序（串行，单 Developer）

```
子模块 1a（HelpScreen 类定义 + CSS + 内容）
    ↓
子模块 1b（BacklogApp.BINDINGS + action_help）
```

### 并行策略

- 两个子模块在同一文件 `app.py` 中，建议由单一 Developer 串行完成，无并行拆分必要。

### 推荐 Developer 分工

| Developer | 负责模块 | 日志文件 |
|-----------|----------|----------|
| Developer-ui | 子模块 1a + 1b（`src/app.py` 全部改动） | `developer-ui.log.md` |

---

## 技术风险与应对

| 风险 | 等级 | 应对方案 |
|------|------|----------|
| `?` 快捷键在 Textual 的键名不确定 | 低 | 参照现有 `"slash"` 用法，使用 `"question_mark"`；如失败可尝试 `"?"` 直接字符串 |
| `HelpScreen` 中 `q` 快捷键与 `BacklogApp` 的 `q`（Quit）冲突 | 低 | ModalScreen 拥有独立的 BINDINGS 作用域，模态层 `q` 不会穿透到 App 层；已有 TrashScreen 使用 `escape` dismiss，HelpScreen 可追加 `q` 绑定 |
| 帮助内容过长导致窗口超出屏幕 | 低 | 设置 `max-height: 85%`，若内容超出可使用 Textual `ScrollableContainer` 包裹 |
| 无数据层改动，迁移/兼容风险 | 无 | 本次改动仅涉及 `app.py`，不改动 `models.py`、`repository.py`、数据库 schema |

---

## 接口约定汇总（供 Developer 参考）

### 新增 Screen 签名

```python
class HelpScreen(ModalScreen[None]):
    def action_dismiss_help(self) -> None: ...
```

### BacklogApp 新增方法签名

```python
def action_help(self) -> None:
    self.push_screen(HelpScreen())
```

### BINDINGS 新增条目（插入位置：现有 `q` 绑定之前）

```python
Binding("question_mark", "help", "Help"),
```

---

- **关联需求：** 查看使用帮助（`?` 快捷键弹出模态帮助窗口）
- **预估复杂度：** 低（单文件，无数据层改动，参照现有 ModalScreen 模式）
- **改动文件：** `src/app.py`（仅此一个文件）
- **后续建议：** 若帮助内容未来增多，可将帮助文本抽取为独立常量或资源文件；当前规模直接内联即可

---

## [TL-9-2] 完整项目技术总结报告（v0.1.0 + v0.2.0）

- **阶段：** 9（项目总结）
- **状态：** completed
- **时间：** 2026-03-12T15:00:00

### 输入

读取 v0.1.0 目录下全部日志文件（含两轮完整开发周期）：
- `tech-leader.log.md`（TL-2-1、TL-2-2、TL-9-1）
- `project-manager.log.md`（PM-2-1、PM-3-1、PM-7-1、PM-9-1、PM-2-2、PM-7-2）
- `developer-core.log.md`（DEV-4-1、DEV-5-1）
- `developer-ui.log.md`（DEV-4-2、DEV-4-3）
- `code-reviewer.log.md`（CR-5-1、CR-5-2、CR-5-3）
- `tester.log.md`（TST-6-1、TST-6-2）
- `customer.log.md`（CUST-7-1、CUST-7-2）

### 输出

---

## 完整技术总结报告：Backlog Manager v0.1.0 → v0.2.0

### 一、两轮开发周期概览

| 版本 | 功能 | 改动文件 | 测试数 | 验收结论 |
|------|------|----------|--------|---------|
| v0.1.0 | 删除二次确认 + 回收站（软删除、180 天保留、恢复、过期清理） | `src/models.py`、`src/repository.py`、`src/app.py`、`tests/test_models.py`、`tests/test_repository.py` | 148（新增 42） | 通过（CUST-7-1） |
| v0.2.0 | 查看使用帮助（`?` 快捷键弹出英文帮助模态窗口） | `src/app.py` | 148（无新增，全量回归通过） | 通过（CUST-7-2） |

---

### 二、架构演进回顾

#### 2.1 现有架构基础（开发前）

项目采用三层清晰分离的架构：

```
src/models.py        ← 数据模型（BacklogItem dataclass + 枚举）
src/repository.py    ← 数据访问层（BacklogRepository + SQLite）
src/app.py           ← TUI 展示层（Textual + ModalScreen 模式）
```

这一架构在两轮开发中均表现出良好的可扩展性：v0.1.0 的软删除改动在各层有对应职责边界，v0.2.0 的帮助窗口仅涉及 TUI 层，完全不触及数据层。

#### 2.2 v0.1.0 架构扩展

**数据模型层（`models.py`）**

- `BacklogItem` 新增 `deleted_at: Optional[datetime] = None` 和 `expires_at: Optional[datetime] = None` 两个可选字段
- `to_dict()` / `from_dict()` 完整支持新字段，向后兼容旧数据（缺失键返回 `None`）
- 设计原则：Model 层不负责设置这两个字段，由 Repository 层托管

**数据访问层（`repository.py`）**

- `delete()` 改为软删除语义（`UPDATE SET deleted_at/expires_at`），外部调用方签名不变
- `list()` / `get()` 默认过滤已删除条目（`WHERE deleted_at IS NULL`），零改动影响现有功能
- 新增 `restore()`、`hard_delete()`、`list_trash()`、`_purge_expired()`、`_migrate_schema()` 方法
- `_migrate_schema()` 使用 `PRAGMA table_info` 检测旧列，确保 schema 迁移幂等，无需手动操作

**TUI 层（`app.py`）**

- 新增两个独立 `ModalScreen` 子类：`ConfirmDeleteScreen[bool]` 和 `TrashScreen[None]`
- `ConfirmDeleteScreen` 通过 `permanent: bool = False` 参数复用于两种场景（软删除确认 / 永久删除确认）
- `TrashScreen` 内嵌套调用 `ConfirmDeleteScreen`（二次确认永久删除），验证了 Textual ModalScreen 支持嵌套 push

#### 2.3 v0.2.0 架构扩展

- 新增 `HelpScreen(ModalScreen[None])`，与现有 Screen 类并列，延续已建立的模式
- 内联 CSS 控制样式，无新增 import，依赖最小化
- 数据层（`models.py`、`repository.py`）零改动，体现了分层架构隔离变化的核心价值

---

### 三、关键技术决策汇总

| 决策 | 版本 | 选型 | 核心理由 | 验证结果 |
|------|------|------|----------|---------|
| 软删除在原表加列，非独立 trash 表 | v0.1.0 | 原表新增 `deleted_at`/`expires_at` 列 | 恢复仅需 UPDATE，无跨表迁移；ID 连续性保留；主界面过滤改动最小 | 实现简洁，CR/Tester/Customer 全部通过 |
| `expires_at` 显式存储 | v0.1.0 | 存入 `deleted_at + 180天` 值 | 清理 SQL 直接使用 `WHERE expires_at <= now()`，性能更好；支持逐条目灵活调整 | P1-3 修复直接受益 |
| `_purge_expired()` 在 Repository `__init__` 同步执行 | v0.1.0 | Repository 层自管理 | 不依赖 TUI 生命周期，单元测试独立；分层边界清晰 | Tester 直接对 Repository 编写独立测试验证 |
| `ConfirmDeleteScreen` 复用，`permanent` 参数区分模式 | v0.1.0（修复） | 单 Screen 类 + 参数分支 | 两种场景布局/按键相同，仅文案不同；默认参数保持向后兼容 | CR-5-2 验证修复正确，无新问题引入 |
| TUI 层单 Developer 串行，不拆分并行 | v0.1.0 | Developer-ui 独立负责 `app.py` 全部改动 | 规避同文件并行编辑冲突风险；单人掌握全文件上下文，集成更顺畅 | DEV-4-2 产出一次通过 CR-5-1 的 TUI 层部分 |
| HelpScreen 内联 CSS + 帮助内容 | v0.2.0 | 直接内联，不抽取资源文件 | 当前内容体量小；与现有 Screen 保持相同的内联 CSS 约定 | CR-5-3 无 P0/P1，一轮通过 |
| `?` 键名使用 `"question_mark"` | v0.2.0 | 参照 `/` → `"slash"` 命名约定 | Textual 特殊字符键名约定一致性 | TST-6-2 验证绑定有效 |

---

### 四、代码审查质量回顾

| 轮次 | 条目 | 关联开发 | P0 | P1 | P2 | 结论 |
|------|------|----------|----|----|----|----|
| 第 1 轮 | CR-5-1 | DEV-4-1 + DEV-4-2 | 1（文案误导） | 3（启动阻塞、返回值丢弃、过期条目未过滤） | 4 | 需修复 |
| 第 2 轮 | CR-5-2 | DEV-5-1（P0/P1 修复） | 0 | 0 | 0 | 通过 |
| 第 3 轮 | CR-5-3 | DEV-4-3（HelpScreen） | 0 | 0 | 3（注释、分隔符 Widget、状态描述措辞） | 通过 |

**关键发现：**

- P0-1（`ConfirmDeleteScreen` 文案误导）本可在技术方案阶段预防：TL-2-1 提出 Screen 复用时，若同时明确"两种场景文案差异"的接口约定，Developer 可直接实现正确版本，避免审查-修复循环
- CR-5-2（第 2 轮）实现了零问题快速收敛，说明 DEV-5-1 的修复质量高
- CR-5-3 对新增功能 HelpScreen 一轮直接通过，得益于：单文件、低复杂度、参照成熟模式

---

### 五、测试覆盖总结

| 测试维度 | v0.1.0 后 | v0.2.0 后 | 说明 |
|----------|-----------|-----------|------|
| 总测试数 | 148 | 148 | v0.2.0 无新增单元测试（HelpScreen 为 TUI 层） |
| 新增测试 | 42 | 0 | v0.1.0 覆盖 models + repository 全部新接口 |
| 全量回归 | 148/148 | 148/148 | 两轮均零失败 |
| TUI 层自动化测试 | 未实现 | 未实现 | 已知限制，记录为技术债务 TD-4 |

**测试覆盖亮点（TST-6-1）：**

- 软删除的完整语义链：`delete → list 不显示 → list_trash 显示 → restore → 重新出现在 list`
- 边界场景：重复删除、`delete/restore` 不存在的条目、`hard_delete` 已软删除的条目
- 幂等性：`_migrate_schema()` 重复调用不报错
- 过期逻辑：`_purge_expired()` 清理过期 + 保留未过期

**TST-6-2 验证策略：**

对于 TUI 组件，采用"import + 反射检查"替代运行时 TUI 测试，验证了类存在性、绑定注册、action 方法存在三个关键点，是在无 Textual 测试框架接入情况下的务实选择。

---

### 六、技术债务全量清单（两轮合并）

| ID | 严重度 | 文件 | 问题描述 | 建议处理时机 |
|----|--------|------|----------|-------------|
| TD-1 | P2 | `src/app.py` | `TrashScreen.action_dismiss_screen` 命名与 Textual 内置 `dismiss()` 相近，易混淆 | 下一次 chore 迭代 |
| TD-2 | P2 | `src/repository.py` | `_row_to_item()` 中 `"deleted_at" in keys` 检查为死代码（`_migrate_schema` 已保证列存在） | 下一次 chore 迭代 |
| TD-3 | P2 | `src/models.py` | `BacklogItem.deleted_at`/`expires_at` 字段缺少注释说明职责边界（由 Repository 层设置） | 下一次 chore 迭代 |
| TD-4 | 中 | `src/app.py` | TUI 层（`ConfirmDeleteScreen`、`TrashScreen`、`HelpScreen`）无 Textual 自动化测试，回归依赖手动验证 | 建议独立迭代补充 |
| TD-5 | P1（已接受） | `src/repository.py` | `_purge_expired()` 每次 Repository 初始化均执行，数据量极大时影响启动延迟 | 数据量增大后处理 |
| TD-6 | 低 | `src/models.py`、`src/repository.py` | `deleted_at`/`expires_at` 使用 naive datetime，跨时区场景 180 天计算可能有轻微偏差 | 多时区需求时处理 |
| TD-7 | P2 | `src/app.py` | `HelpScreen` 中 `q` 绑定的 `show=False` 行为未加注释说明（P2-5） | 下一次 chore 迭代 |
| TD-8 | P2 | `src/app.py` | `HelpScreen.compose()` 使用硬编码 Unicode 分隔符，可改用 Textual 内置 `Rule()` widget（P2-6） | 低优先级 |
| TD-9 | P2 | `src/app.py` | `HelpScreen` 帮助文本硬编码在 `compose()` 中，快捷键增减时需同步维护，存在内容过时风险 | 快捷键列表增多后处理 |

---

### 七、后续建议（综合两轮）

#### 短期（下一个迭代优先）

1. **补充 TUI 层自动化测试**（TD-4）
   - 使用 Textual `App.run_test()` 为 `ConfirmDeleteScreen`、`TrashScreen`、`HelpScreen` 编写自动化测试
   - 关键场景：弹窗触发/取消、回收站恢复后主界面刷新、永久删除二次确认、`?` 弹出帮助窗口

2. **处理 P2 技术债务批量 chore**（TD-1、TD-2、TD-3、TD-7、TD-8）
   - 重命名 `action_dismiss_screen`、简化 `_row_to_item()` 防御检查、添加字段注释、`HelpScreen` 注释补充
   - 改动量小，建议集中在一次 chore PR 中处理

3. **修正 HelpScreen 状态循环描述**（TD-9 部分）
   - 将 `s` 键说明从 `"Toggle status: Todo → In Progress → Done → In Progress"` 改为更精确的表述（P2-7 建议）

#### 中期（架构优化）

4. **回收站"一键清空"功能**
   - `TrashScreen` 新增快捷键（如 `Shift+X`），`Repository` 新增 `hard_delete_all_trash()` 方法

5. **`_purge_expired()` 频率限制**（TD-5）
   - 记录 `last_purge_at`（存入 SQLite metadata 表或配置文件），超过 24 小时未清理才触发

6. **回收站数据量优化**
   - 在 `deleted_at` 列建索引（`CREATE INDEX IF NOT EXISTS idx_deleted_at ON backlog_items(deleted_at)`）

#### 长期（架构演进）

7. **时区支持**（TD-6）
   - 统一改为 UTC 时间存储（`datetime.utcnow()`），展示层本地化转换；需要数据迁移脚本

8. **帮助内容外部化**（TD-9）
   - 若快捷键列表持续增多，将帮助文本抽取为独立常量模块或 Markdown 资源文件，保持 `compose()` 简洁

9. **回收站保留期可配置化**
   - 引入配置文件（如 `~/.config/backlog/settings.toml`），允许用户自定义保留天数，取代硬编码的 180 天

---

### 八、整体开发过程评估

| 维度 | 评估 |
|------|------|
| 架构可扩展性 | 良好。三层分离架构支撑了两轮完全不同复杂度的功能迭代，数据层改动不扩散到 TUI 层，TUI 层新增 Screen 不影响数据层 |
| 代码审查效率 | 高效。v0.1.0 两轮、v0.2.0 一轮即收敛。代码审查识别出了技术方案阶段未覆盖的边界场景（P0-1 文案误导、P1-3 过期过滤） |
| 测试覆盖质量 | 数据层充分（42 个新增测试，全部边界场景覆盖）；TUI 层仅静态验证，为已知技术债务 |
| 多 Agent 协作效率 | 日志直通通信机制有效减少 Master 中转。Developer-core 与 Developer-ui 分工清晰；CodeReviewer ↔ Developer 的审查-修复循环高效收敛 |
| 风险控制 | 所有预识别风险均未实际发生；审查阶段新发现 3 个问题（1 P0 + 2 P1），全部在合并前修复 |
| 版本管理 | 遵循 Semantic Versioning 2.0.0，v0.1.0（功能新增）→ v0.2.0（功能新增，minor 递增），语义清晰 |

**总体评估：** 两轮开发均高质量完成，架构设计经受了两次功能扩展的检验，无重大技术债务引入，客户验收 100% 通过（CUST-7-1、CUST-7-2）。技术债务以 P2 级别为主，不影响系统稳定性和功能正确性。

---

- **覆盖版本：** v0.1.0、v0.2.0
- **总结日期：** 2026-03-12
- **总测试数：** 148（全部通过）
- **客户验收：** 2 次，均通过
- **未解决 P0/P1：** 0
- **技术债务条目：** 9 条（均为 P2 或已接受的 P1）

---
