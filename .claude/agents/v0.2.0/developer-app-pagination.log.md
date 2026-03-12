## [DEV-4-2] 为 BacklogApp 主列表和 TrashScreen 回收站添加翻页功能

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-12T00:00:00

### 输入

读取了 `.claude/agents/v0.2.0/tech-leader.log.md`，了解翻页功能设计：
- BacklogApp：page/page_size 实例变量，`n`/`p` 键绑定，`_refresh_table()` 加 LIMIT/OFFSET，`_refresh_stats()` 显示页码，过滤器变更重置 page=0
- TrashScreen：同上，`_refresh_trash()` 加 keyword/LIMIT/OFFSET，restore/hard_delete 后检查页码是否需要回退

读取了 `.claude/agents/v0.2.0/developer-repository.log.md`，了解 repository 层接口约定：
- `repo.list(..., limit, offset)` — 主列表分页
- `repo.count(status, category, keyword)` — 主列表总数
- `repo.list_trash(keyword, limit, offset)` — 回收站分页
- `repo.count_trash(keyword)` — 回收站总数

### 输出

**修改文件：** `src/app.py`

**改动说明：**

#### 1. BacklogApp — 翻页状态变量（`__init__`）

新增两个实例变量：
```python
self.page: int = 0
self.page_size: int = 20
```

#### 2. BacklogApp — 键绑定（`BINDINGS`）

新增两条绑定：
```python
Binding("n", "next_page", "Next Page"),
Binding("p", "prev_page", "Prev Page"),
```

#### 3. BacklogApp — `_refresh_table()` 分页查询

调用 `repo.list()` 时增加 `limit=self.page_size, offset=self.page * self.page_size` 参数，实现后端分页。

#### 4. BacklogApp — `_refresh_stats()` 页码显示

新增调用 `repo.count()` 获取当前过滤条件下的总数，计算总页数并追加到状态栏：
```
... | Page 1/3  [N]ext  [P]rev
```

#### 5. BacklogApp — 过滤器变更重置页码

在 `on_status_filter()` 和 `on_category_filter()` 中调用 `_refresh_table()` 前重置 `self.page = 0`。

在 `action_search()` 的回调中同样重置 `self.page = 0`。

#### 6. BacklogApp — 翻页 action 方法

新增 `action_next_page()` 和 `action_prev_page()`：
- next：检查是否已是最后页，否则 `self.page += 1` 后刷新
- prev：检查是否已是第一页，否则 `self.page -= 1` 后刷新
- 边界时显示 warning notify

#### 7. TrashScreen — 翻页状态变量（`__init__`）

新增实例变量：
```python
self.page: int = 0
self.page_size: int = 20
```

#### 8. TrashScreen — 键绑定（`BINDINGS`）

新增：
```python
Binding("n", "next_page", "Next Page"),
Binding("p", "prev_page", "Prev Page"),
```

#### 9. TrashScreen — `_refresh_trash()` 分页 + 页码显示

- 使用 `getattr(self, 'search_keyword', None)` 兼容 search_keyword 属性（由 developer-app-trash 模块添加）
- 调用 `repo.list_trash(keyword=keyword, limit=self.page_size, offset=self.page * self.page_size)`
- 计算总页数并更新 `#trash-hint` 显示页码信息
- 同时将 `deleted_at` 格式从 `%Y-%m-%d %H:%M` 改为 `%Y-%m-%d %H:%M:%S`（模块B的改动合并于此）

#### 10. TrashScreen — restore/hard_delete 后回退页码

在 `action_restore_item()` 和 `action_hard_delete_item()` 的成功回调中：
- 重新计算 `count_trash(keyword=keyword)` 得到新总页数
- 如果 `self.page >= total_pages`，回退到 `max(0, total_pages - 1)`

#### 11. TrashScreen — 翻页 action 方法

新增 `action_next_page()` 和 `action_prev_page()`，逻辑同 BacklogApp。

#### 12. HelpScreen — 翻页快捷键说明

在 Navigation 部分新增：
```
   n              Next page
   p              Previous page
```

**验证：** `python3 -c "import sys; sys.path.insert(0, 'src'); import app; print('Import OK')"` → 导入成功，无语法错误。

---

## [DEV-5-1] 修复 CodeReviewer P1/P2 问题：count 缓存、统计口径统一、帮助文档补全

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-12T10:00:00

### 输入

读取了 `.claude/agents/v0.2.0/code-reviewer.log.md`（CR-5-1），需修复以下问题：
- P1-1：BacklogApp.action_next_page 重复调用 count()
- P1-2：TrashScreen.action_next_page 重复调用 count_trash()
- P1-3：_refresh_stats() 中 Total 使用 get_stats() 的无过滤总数，与分页的过滤总数语义不一致
- P2-3：HelpScreen Trash 分区缺少 / 搜索快捷键说明

### 输出

**修改文件：** `src/app.py`

**改动说明：**

#### 1. P1-1 修复 — BacklogApp._total_count 缓存

在 `BacklogApp.__init__` 中新增：
```python
self._total_count: int = 0
```

在 `_refresh_stats()` 中将 `total_count` 赋值改为写入 `self._total_count`：
```python
self._total_count = self.repo.count(status=..., category=..., keyword=...)
```

在 `action_next_page()` 中直接使用 `self._total_count`，删除重复的 `repo.count()` 调用：
```python
def action_next_page(self) -> None:
    total_pages = max(1, (self._total_count + self.page_size - 1) // self.page_size)
    ...
```

#### 2. P1-2 修复 — TrashScreen._total_count 缓存

在 `TrashScreen.__init__` 中新增：
```python
self._total_count: int = 0
```

在 `_refresh_trash()` 中将 `count_trash()` 结果赋值给 `self._total_count`：
```python
total = self.repo.count_trash(keyword=keyword)
self._total_count = total
```

在 `action_next_page()` 中直接使用 `self._total_count`，删除重复的 `repo.count_trash()` 调用。

#### 3. P1-3 修复 — 统计口径统一

在 `_refresh_stats()` 的 stats bar 中，将 `Total` 数据源从 `stats['total']`（get_stats 返回，不含 status/keyword 过滤）改为 `self._total_count`（count() 返回，包含所有过滤条件）：
```python
f" Total: {self._total_count}  |  "
```
这样 Total 与 Page x/y 的计算基准完全一致，不会出现"Total: 100 | Page 1/1"的语义矛盾。

#### 4. P2-3 修复 — HelpScreen 补全回收站搜索说明

在 HelpScreen Trash 分区新增一行：
```python
yield Label("   / (in Trash)   Search trash items")
```

**验证：** `python3 -c "import sys; sys.path.insert(0, 'src'); import app; print('Import OK')"` → 导入成功，无语法错误。

---
