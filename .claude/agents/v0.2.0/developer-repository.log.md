## [DEV-4-1] 扩展 repository.py：分页与回收站搜索支持

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-12T00:00:00

### 输入

读取了 `.claude/agents/v0.2.0/tech-leader.log.md`，了解到：
- repository.py 需要在 list() 添加 limit/offset 分页参数
- 需新增 count() 方法，与 list() 共享 WHERE 条件（抽取 _build_where_clause()）
- list_trash() 需添加 keyword 搜索 + limit/offset 分页
- 需新增 count_trash() 方法，与 list_trash() 共享 WHERE 条件（抽取 _build_trash_where_clause()）

### 输出

**修改文件：** `src/repository.py`

**改动说明：**

1. **新增 `_build_where_clause()` 私有方法**（第 104-124 行）
   - 将 list() 中原有的 WHERE 条件构建逻辑提取为独立方法
   - 参数：`status`, `category`, `keyword`（均为 Optional）
   - 返回：`tuple[str, List[Any]]`，即 (WHERE子句字符串, 参数列表)
   - 固定基础条件：`deleted_at IS NULL`

2. **新增 `_build_trash_where_clause()` 私有方法**（第 126-139 行）
   - 封装回收站查询的 WHERE 条件
   - 参数：`keyword: Optional[str] = None`
   - 固定条件：`deleted_at IS NOT NULL AND (expires_at IS NULL OR expires_at > ?)`（内部计算 now）
   - keyword 存在时追加：`AND (title LIKE ? OR description LIKE ?)`

3. **扩展 `list()` 方法**（第 141-157 行）
   - 新增参数：`limit: Optional[int] = None`, `offset: int = 0`
   - 内部改为调用 `_build_where_clause()` 共享条件构建
   - limit 不为 None 时追加 `LIMIT ? OFFSET ?` 到 SQL
   - 向后兼容：不传 limit 时行为与原实现完全一致

4. **新增 `count()` 方法**（第 159-168 行）
   - 参数：`status`, `category`, `keyword`（均为 Optional）
   - 复用 `_build_where_clause()` 确保 WHERE 条件与 list() 完全同步
   - SQL：`SELECT COUNT(*) FROM backlog_items WHERE {where}`
   - 返回 int

5. **扩展 `list_trash()` 方法**（第 235-250 行）
   - 新增参数：`keyword: Optional[str] = None`, `limit: Optional[int] = None`, `offset: int = 0`
   - 内部改为调用 `_build_trash_where_clause()` 共享条件构建
   - limit 不为 None 时追加分页子句
   - 向后兼容：无参调用行为与原实现完全一致

6. **新增 `count_trash()` 方法**（第 252-259 行）
   - 参数：`keyword: Optional[str] = None`
   - 复用 `_build_trash_where_clause()` 确保与 list_trash() 条件同步
   - SQL：`SELECT COUNT(*) FROM backlog_items WHERE {where}`
   - 返回 int

**接口约定（供 app 层开发者参考）：**

```python
# 主列表分页查询
repo.list(status=..., category=..., keyword=..., limit=20, offset=0)

# 主列表总数（用于计算总页数）
repo.count(status=..., category=..., keyword=...)

# 回收站分页 + 关键字搜索
repo.list_trash(keyword="...", limit=20, offset=0)

# 回收站总数
repo.count_trash(keyword="...")
```

---
