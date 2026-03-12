## [DEV-4-3] TrashScreen 搜索功能 + 删除时间精度修正

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-12T00:00:00

### 输入

读取了 `.claude/agents/v0.2.0/tech-leader.log.md`，了解模块 B（删除时间精度）和模块 C（回收站搜索）的设计方案。

读取了 `.claude/agents/v0.2.0/developer-repository.log.md`，确认 repository 层已提供以下接口：
- `repo.list_trash(keyword=..., limit=..., offset=...)` — 支持关键字搜索和分页
- `repo.count_trash(keyword=...)` — 支持关键字过滤的总数查询

注：另一个 Developer（app-pagination）已先行修改了 `src/app.py`，在 `TrashScreen` 中添加了翻页功能，并预留了 `getattr(self, 'search_keyword', None)` 的调用占位，等待本模块注入 `search_keyword` 属性。

### 输出

**修改文件：** `src/app.py`

**改动说明：**

1. **TrashScreen.BINDINGS 新增 `slash` 绑定**（第 298 行）
   - 新增：`Binding("slash", "search_trash", "Search")`
   - 位置：在 `x` 和 `n` 之间插入

2. **TrashScreen.__init__ 初始化 `search_keyword`**（第 309 行）
   - 新增：`self.search_keyword: Optional[str] = None`
   - 将之前翻页开发者预留的 `getattr(self, 'search_keyword', None)` 调用全部替换为直接属性访问 `self.search_keyword`

3. **删除时间格式修正**（第 336 行）
   - 已由 app-pagination 开发者修正为 `%Y-%m-%d %H:%M:%S`，本次确认保留无需重复修改

4. **`#trash-hint` 添加搜索提示**（第 351 行）
   - 在 hint 文本中追加 `[bold][/][/bold] Search`，格式为：
     `[R] Restore | [X] Delete Forever | [/] Search | [Esc] Close | Page x/y [N] Next [P] Prev`

5. **新增 `action_search_trash()` 方法**（第 404-415 行）
   - 调用 `self.app.push_screen(SearchScreen(), callback=on_result)` 复用已有 SearchScreen modal
   - 回调中设置 `self.search_keyword`（空字符串转为 None），重置 `self.page = 0`，调用 `_refresh_trash()`
   - 搜索有词时 notify `Filter: '{keyword}'`，清除时 notify `Filter cleared`

6. **清理所有 `getattr` 占位**
   - `_refresh_trash()`、`action_restore_item()`、`action_hard_delete_item()`、`action_next_page()` 中的 `getattr(self, 'search_keyword', None)` 全部替换为 `self.search_keyword`

**接口对接确认：**
- `_refresh_trash()` 调用：`self.repo.list_trash(keyword=self.search_keyword, limit=..., offset=...)`
- `count_trash()` 调用：`self.repo.count_trash(keyword=self.search_keyword)`

---
