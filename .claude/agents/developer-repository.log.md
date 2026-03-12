## [DEV-4-2] 实现 Backlog 数据存储层（repository 模块）

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-11T22:45:00

### 输入
根据 TL-2-1 技术方案中模块 2 的接口定义，实现 `BacklogRepository` 类。依赖已完成的 `src/models.py`（DEV-4-1）中的 `BacklogItem`、`Status`、`Priority`。

### 输出

#### 改动说明

创建 `src/repository.py`，实现基于 SQLite 的 `BacklogRepository` 类，完整覆盖 TechLeader 定义的所有接口：

| 方法 | 说明 |
|------|------|
| `__init__(db_path)` | 初始化 SQLite 连接（`row_factory=sqlite3.Row`），自动创建 `backlog_items` 表 |
| `create(item)` | INSERT 并设置 `item.id = lastrowid`，返回带 ID 的 item |
| `get(item_id)` | 按 ID 查询，不存在返回 None |
| `list(status, category, keyword)` | 动态拼接 WHERE 条件，keyword 对 title/description 做 LIKE 模糊匹配 |
| `update(item_id, **fields)` | 仅更新 allowed 字段集合（title/description/status/category/priority），自动更新 updated_at |
| `delete(item_id)` | 按 ID 删除，返回 bool 表示是否成功 |
| `transition_status(item_id, new_status)` | 含状态流转校验：TODO↔IN_PROGRESS↔DONE，非法转换抛 ValueError |
| `get_categories()` | 返回去重排序后的非空分类列表 |
| `get_stats(category)` | 返回 total、by_status、by_priority 统计字典，支持按分类过滤 |
| `close()` | 关闭数据库连接 |

#### 关键设计决策
- 使用 `sqlite3.Row` 作为 row_factory，便于按列名访问
- 状态流转校验在 repository 层统一处理，允许回退（DONE→IN_PROGRESS, IN_PROGRESS→TODO）
- update 方法自动处理 Status/Priority 枚举到字符串的转换
- 仅使用 Python 内置 sqlite3，零外部依赖

#### 修改的文件
- **新增** `src/repository.py` — BacklogRepository 类完整实现

---
