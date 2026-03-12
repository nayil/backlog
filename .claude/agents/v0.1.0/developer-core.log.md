## [DEV-4-1] 数据层实现：BacklogItem 软删除字段 + Repository 回收站接口

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-12T00:00:00

### 输入

读取 `tech-leader.log.md`（TL-2-1）中的模块 1 + 模块 2 规格，实现数据模型扩展和数据库层回收站功能。

### 输出

#### 改动说明

**目标：** 为 BacklogItem 增加软删除支持，同时保持对旧数据库（无新列）的向后兼容性。

**改动文件：** `src/models.py`、`src/repository.py`

---

#### src/models.py

**变更：**
1. `BacklogItem` dataclass 新增两个字段（默认值均为 `None`，不破坏现有构造调用）：
   - `deleted_at: Optional[datetime] = None`
   - `expires_at: Optional[datetime] = None`
2. `to_dict()` 新增两个键 `deleted_at`、`expires_at`，值为 ISO 字符串或 `None`
3. `from_dict()` 新增对 `deleted_at`、`expires_at` 的解析（安全地处理键不存在的情况）

---

#### src/repository.py

**变更：**

| 位置 | 变更内容 |
|------|---------|
| `import` | 新增 `timedelta` |
| `__init__()` | 在 `_create_table()` 后依次调用 `_migrate_schema()` 和 `_purge_expired()` |
| `_create_table()` | 建表 SQL 新增 `deleted_at TEXT DEFAULT NULL`、`expires_at TEXT DEFAULT NULL` 两列 |
| `_migrate_schema()` | 新增方法：用 `PRAGMA table_info` 检测列是否存在，不存在则 `ALTER TABLE ADD COLUMN`，确保旧数据库兼容 |
| `_row_to_item()` | 读取 `deleted_at`、`expires_at`，兼容旧行（列不在 `row.keys()` 时或值为 NULL 时均返回 `None`） |
| `get()` | 新增 `include_deleted=False` 参数；默认查询加 `AND deleted_at IS NULL` |
| `list()` | 基础过滤条件从 `WHERE 1=1` 改为 `WHERE deleted_at IS NULL` |
| `delete()` | 改为软删除：`UPDATE SET deleted_at=now, expires_at=now+180d WHERE id=? AND deleted_at IS NULL`；返回语义不变（bool） |
| `restore()` | 新增：`UPDATE SET deleted_at=NULL, expires_at=NULL WHERE id=? AND deleted_at IS NOT NULL`，成功则返回恢复后的 `BacklogItem` |
| `hard_delete()` | 新增：`DELETE FROM backlog_items WHERE id=?`，返回 bool |
| `list_trash()` | 新增：查询 `deleted_at IS NOT NULL ORDER BY deleted_at DESC`，返回已软删除条目列表 |
| `_purge_expired()` | 新增：`DELETE WHERE expires_at IS NOT NULL AND expires_at <= now()`，在 `__init__` 中同步执行 |
| `get_categories()` | 过滤条件加 `AND deleted_at IS NULL`，不统计已删除条目的分类 |
| `get_stats()` | 基础条件改为 `FROM backlog_items WHERE deleted_at IS NULL`，统计不含回收站条目 |

**向后兼容保障：**
- `_migrate_schema()` 保证旧数据库在首次启动后自动获得新列
- `_row_to_item()` 对 `deleted_at`/`expires_at` 做防御性检查，不会因旧行缺少这些列而崩溃
- `delete()` 签名和返回类型不变，调用方无需修改

---

## [DEV-5-1] 修复 CodeReviewer 审查发现的 P0 和 P1 问题

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-12T01:00:00

### 输入

读取 `.claude/agents/v0.1.0/code-reviewer.log.md`（CR-5-1），针对 P0-1、P1-2、P1-3 进行修复。

### 输出

#### 改动说明

**目标：** 修复 CodeReviewer 报告的 P0 和 P1 问题，提升功能正确性和用户体验。

---

#### 修复 1：P0-1 — ConfirmDeleteScreen 文案在永久删除场景下误导用户

**文件：** `src/app.py`

**问题：** `ConfirmDeleteScreen` 硬编码"Move to Trash?"和"可在 180 天内恢复"文案，但 `TrashScreen.action_hard_delete_item()` 也使用同一 Screen，导致用户在永久删除时看到错误提示。

**修复：**
- `ConfirmDeleteScreen.__init__` 新增 `permanent: bool = False` 参数
- `compose()` 根据 `permanent` 值动态显示：
  - `permanent=False`（默认）：标题 "Move to Trash?"，说明 "The item will be moved to trash and can be restored within 180 days."
  - `permanent=True`：标题 "Delete Forever?"，说明 "This action cannot be undone."
- `TrashScreen.action_hard_delete_item()` 中调用 `ConfirmDeleteScreen(title, permanent=True)`

---

#### 修复 2：P1-2 — action_delete_item() 丢弃 repo.delete() 的返回值

**文件：** `src/app.py`

**问题：** `self.repo.delete(item_id)` 返回值被忽略，软删除失败时界面仍显示"Item moved to trash"，产生虚假反馈。

**修复：**
- 捕获 `delete()` 返回值 `success`
- `success=True` 时通知"Item moved to trash"
- `success=False` 时通知"Delete failed"（severity="error"）

---

#### 修复 3：P1-3 — list_trash() 未过滤过期条目

**文件：** `src/repository.py`

**问题：** `list_trash()` 仅过滤 `deleted_at IS NOT NULL`，未过滤已过期条目（`expires_at <= now()`）。应用长时间运行时，已过期但未被 `_purge_expired()` 清理的条目会出现在回收站列表中。

**修复：**
- SQL 改为 `WHERE deleted_at IS NOT NULL AND (expires_at IS NULL OR expires_at > ?)`，传入当前时间
- docstring 与实现保持一致（"have not yet expired"）

---