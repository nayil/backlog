## [TL-2-1] 技术方案设计：翻页、删除时间精度、回收站搜索

- **阶段：** 2
- **状态：** completed
- **时间：** 2026-03-12T00:00:00

### 输入

需求描述：
1. 翻页功能：主列表和回收站在条目过多时支持分页浏览（上一页/下一页）
2. 回收站删除时间精确到秒：deleted_at 显示格式从 %Y-%m-%d %H:%M 改为 %Y-%m-%d %H:%M:%S
3. 回收站搜索功能：回收站内支持按关键字搜索（搜索 title 和 description）

目标文件：src/app.py, src/repository.py, src/models.py, tests/test_repository.py

### 输出

---

## 技术方案概述

经代码调研，现有架构如下：

- **models.py**：纯数据类，无需修改
- **repository.py**：`list()` 已支持 keyword 过滤；`list_trash()` 无 keyword 参数，无分页支持
- **app.py**：
  - `BacklogApp`：主界面，调用 `repo.list()` 做前端全量加载，`#stats-bar` 作为底部状态栏
  - `TrashScreen`：弹出 ModalScreen，调用 `repo.list_trash()` 全量加载，底部 `#trash-hint` 为操作提示

三项改动互相独立，可拆为三个模块并行开发。

---

## 模块划分

### 模块 A：翻页功能（Pagination）

**职责：** 在主列表（`BacklogApp`）和回收站（`TrashScreen`）中实现分页浏览。

**设计决策：后端分页（repository 层 LIMIT/OFFSET）**

选择后端分页而非前端分页的原因：
- 数据量可能增长，前端分页每次加载全量数据不经济
- 现有 `list()` 和 `list_trash()` 均返回 `List[BacklogItem]`，改为 LIMIT/OFFSET 只需增加两个可选参数
- 页码状态由 UI 层持有，repository 层保持无状态

**repository.py 接口变更：**

```python
# list() 新增参数
def list(
    self,
    status: Optional[Status] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: Optional[int] = None,   # 新增
    offset: int = 0,               # 新增
) -> List[BacklogItem]: ...

# list() 需配套 count() 方法，用于计算总页数
def count(
    self,
    status: Optional[Status] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
) -> int: ...

# list_trash() 新增参数
def list_trash(
    self,
    keyword: Optional[str] = None,   # 与模块C共用，见下文
    limit: Optional[int] = None,     # 新增
    offset: int = 0,                 # 新增
) -> List[BacklogItem]: ...

# list_trash() 配套 count_trash() 方法
def count_trash(
    self,
    keyword: Optional[str] = None,
) -> int: ...
```

**app.py 变更（BacklogApp）：**

- 新增实例变量：`self.page: int = 0`，`self.page_size: int = 20`
- `_refresh_table()` 调用时传入 `limit=self.page_size, offset=self.page * self.page_size`
- `_refresh_stats()` 扩展：在 `#stats-bar` 中追加页码信息，格式为 `| Page: {current}/{total_pages}`
- 新增 BINDINGS：
  - `Binding("n", "next_page", "Next Page")`
  - `Binding("p", "prev_page", "Prev Page")`
- 新增 action：`action_next_page()` / `action_prev_page()`，修改 `self.page` 后调用 `_refresh_table()`
- 过滤条件变更时重置 `self.page = 0`

**app.py 变更（TrashScreen）：**

- 新增实例变量：`self.page: int = 0`，`self.page_size: int = 20`
- 新增实例变量：`self.search_keyword: Optional[str] = None`（与模块C共用）
- `_refresh_trash()` 调用时传入 `keyword=self.search_keyword, limit=self.page_size, offset=self.page * self.page_size`
- 更新 `#trash-hint` 内容，追加页码信息和翻页快捷键提示
- 新增 BINDINGS：
  - `Binding("n", "next_page", "Next Page")`
  - `Binding("p", "prev_page", "Prev Page")`
- 新增 action：`action_next_page()` / `action_prev_page()`

**页码显示格式（底部状态栏/hint）：**

- BacklogApp `#stats-bar`：`... | Page: 1/3  [N] Next  [P] Prev`（总页数=1时隐藏翻页提示，或始终显示）
- TrashScreen `#trash-hint`：原有操作提示后追加 `| Page: 1/2  [N] Next  [P] Prev`

**依赖关系：** 模块A依赖模块C对 `list_trash()` 签名的扩展（keyword 参数），建议A与C合并在 repository 层一次性修改，或A直接加入 keyword 参数预留位置。

---

### 模块 B：删除时间精度（Timestamp Precision）

**职责：** 将 `TrashScreen._refresh_trash()` 中 `deleted_at` 的 strftime 格式从 `%Y-%m-%d %H:%M` 改为 `%Y-%m-%d %H:%M:%S`。

**变更范围极小，仅涉及 app.py 第 325 行：**

```python
# 原
deleted_str = item.deleted_at.strftime("%Y-%m-%d %H:%M") if item.deleted_at else "-"
# 改为
deleted_str = item.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if item.deleted_at else "-"
```

**依赖关系：** 无外部依赖，可独立实现。

---

### 模块 C：回收站搜索（Trash Search）

**职责：** 在 `TrashScreen` 中添加关键字搜索入口，并在 repository 层扩展 `list_trash()` 支持 keyword 过滤。

**repository.py 接口变更：**

```python
def list_trash(
    self,
    keyword: Optional[str] = None,  # 新增：搜索 title 和 description
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[BacklogItem]: ...
```

SQL 扩展：在现有 WHERE 子句后追加 `AND (title LIKE ? OR description LIKE ?)` 条件（与 `list()` 的关键字过滤逻辑一致）。

**app.py 变更（TrashScreen）：**

- 新增实例变量：`self.search_keyword: Optional[str] = None`
- 新增 BINDING：`Binding("slash", "search_trash", "Search")`
- 新增 action：`action_search_trash()`，推送 `SearchScreen`（复用现有 `SearchScreen` 弹窗），回调中更新 `self.search_keyword` 并调用 `_refresh_trash()`
- 搜索状态变更时重置翻页 `self.page = 0`
- 更新 `#trash-hint` 显示当前搜索关键字（如 `Filter: "keyword"`）

**依赖关系：** 模块C的 repository 层修改（list_trash keyword 参数）是模块A分页的前置条件，建议C的 repository 层优先实现。

---

## 接口依赖图

```
models.py (无变更)
    ↓
repository.py
  - list(... limit, offset)        ← 模块A
  - count(...)                     ← 模块A
  - list_trash(keyword, limit, offset) ← 模块A + 模块C
  - count_trash(keyword)           ← 模块A + 模块C
    ↓
app.py
  - BacklogApp: 翻页状态+绑定+stats-bar显示  ← 模块A
  - TrashScreen: 翻页状态+绑定               ← 模块A
  - TrashScreen: deleted_at格式修正          ← 模块B
  - TrashScreen: 搜索入口+状态               ← 模块C
```

---

## 开发计划

### 阶段 4 模块划分与并行策略

| 模块 | 文件 | 依赖 | 并行策略 |
|------|------|------|----------|
| **模块 A+C（repository层）** | repository.py | 无 | 先行，单开发者完成 repository 层的全部扩展（list/count/list_trash/count_trash） |
| **模块 B** | app.py (TrashScreen._refresh_trash 一行) | 无 | 可与 repository 层并行，但改动极小，可合并入模块 C 的 app.py 开发 |
| **模块 A（app层）** | app.py (BacklogApp + TrashScreen 翻页) | 依赖 repository 层 | repository 层完成后开发 |
| **模块 C（app层）** | app.py (TrashScreen 搜索) | 依赖 repository 层 | repository 层完成后，可与模块A的app层并行（两人分别修改不同方法） |

**建议执行顺序：**

1. **串行第一步**：单个 Developer 完成 `repository.py` 扩展（list + count + list_trash + count_trash），写入 `developer-repository.log.md`
2. **并行第二步**：
   - Developer-app-pagination：实现 `BacklogApp` 和 `TrashScreen` 翻页（读取 repository developer 日志获取接口约定），写入 `developer-app-pagination.log.md`
   - Developer-app-trash：实现 `TrashScreen` 搜索 + deleted_at 格式修正（模块B+C的app层），写入 `developer-app-trash.log.md`

---

## 技术风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| TrashScreen 的 BINDINGS 中 `n`/`p` 与现有按键冲突 | 中 | 检查现有 BINDINGS，`n` 和 `p` 目前未被占用，可安全使用 |
| BacklogApp 中 `n` 键可能与其他操作混淆 | 低 | 同上检查；或改用 `ctrl+right`/`ctrl+left` 等组合键，保持与主流 TUI 习惯一致 |
| 过滤条件变化时未重置页码导致空页 | 中 | 所有触发 `_refresh_table()` 的过滤条件变更处均需 `self.page = 0` |
| count() 与 list() 的 SQL WHERE 条件需保持同步 | 中 | 建议抽取 `_build_where_clause()` 私有方法共用，避免两处维护 |
| 翻页后光标位置 | 低 | DataTable.clear() 后重新加载，光标自动归零，用户体验可接受 |

---

### 输入总结
需求已明确，三项功能独立性高，repository 层是 app 层的前置依赖，建议优先开发 repository 扩展后并行推进 app 层改动。

---

## [TL-9-1] v0.2.0 技术总结报告

- **阶段：** 9
- **状态：** completed
- **时间：** 2026-03-12T14:00:00Z

### 输入

读取了 `.claude/agents/v0.2.0/` 下所有日志文件：
- `tech-leader.log.md`（TL-2-1）：本轮技术方案
- `project-manager.log.md`（PM-2-1、PM-3-1、PM-7-1）：项目计划、可行性评估、Release Note
- `developer-repository.log.md`（DEV-4-1）：repository 层扩展
- `developer-app-pagination.log.md`（DEV-4-2、DEV-5-1）：翻页功能实现与 P1/P2 修复
- `developer-app-trash.log.md`（DEV-4-3）：回收站搜索与时间格式修正
- `code-reviewer.log.md`（CR-5-1）：代码审查报告
- `tester.log.md`（TST-6-1）：测试报告（75/75 通过）
- `customer.log.md`（CUST-7-1）：客户验收报告（通过）

### 输出

---

## v0.2.0 技术总结报告

### 一、架构决策回顾

#### 1. 后端分页方案选型（LIMIT/OFFSET vs 前端全量加载）

**决策：选择后端分页（repository 层 LIMIT/OFFSET）**

- **理由**：主列表和回收站数据量潜在无上界，前端全量加载对大数据集不经济；后端分页将数据裁剪下推至 SQLite，仅返回当前页所需记录。
- **实现**：`list()` 和 `list_trash()` 各新增 `limit`、`offset` 可选参数，默认值保持向后兼容；配套新增 `count()` 和 `count_trash()` 计算总页数，UI 层持有页码状态（`self.page`），repository 层保持无状态。
- **回顾评价**：决策正确。后端分页使 repository API 的扩展范围明确，UI 层只需维护一个整数 `self.page`，复杂度分配合理。向后兼容设计（所有新参数均有默认值）也使现有调用方无需改动，验收测试覆盖了向后兼容场景并全部通过。

#### 2. WHERE 子句共享（`_build_where_clause()` 私有方法抽取）

**决策：将 `list()` 与 `count()` 的 WHERE 构建逻辑统一提取到 `_build_where_clause()`，`list_trash()` 与 `count_trash()` 同理提取到 `_build_trash_where_clause()`**

- **触发背景**：CodeReviewer 在 P1-3 中指出，若 `count()` 与 `list()` 的 WHERE 子句独立维护，后续新增过滤条件时极易出现两处不同步、导致总页数计算与实际数据集大小不一致的 bug。TechLeader 在方案设计阶段已识别该风险并将其列为"建议"，PM 在阶段 3 评估时将其升级为"开发规范要求"。
- **实现**：developer-repository 实际执行中按规范要求落地，两个私有方法返回 `(where_clause: str, params: List[Any])`，`list`/`count` 和 `list_trash`/`count_trash` 各自复用，无重复 SQL 片段。
- **回顾评价**：该设计在整个开发、审查和测试阶段均未出现 count 与 list 数据不一致的问题，验证了决策的有效性。这是本版本在可维护性层面最重要的一个架构决策。

#### 3. 回收站搜索：复用现有 SearchScreen 弹窗

**决策：TrashScreen 的搜索入口复用主列表已有的 `SearchScreen` modal，而非新建独立弹窗**

- **理由**：`SearchScreen` 已实现关键字输入和回调机制，行为完全满足回收站搜索需求，复用可减少 UI 组件数量，降低后续维护成本。
- **回顾评价**：实现顺利，未发现复用带来的副作用。Customer 验收确认搜索与翻页联动（搜索后重置页码）逻辑正确。

#### 4. 并行开发策略：repository 先行，app 层并行

**决策：先串行完成 repository 层全部扩展（DEV-4-1），再并行开发两个 app 层模块（DEV-4-2、DEV-4-3）**

- **理由**：app 层翻页（DEV-4-2）和回收站搜索（DEV-4-3）均依赖 repository 新接口；两个 app 层模块分别聚焦 `BacklogApp` 和 `TrashScreen`，方法级别无重叠，可安全并行。
- **接口协调**：developer-app-pagination 提前以 `getattr(self, 'search_keyword', None)` 占位，等待 developer-app-trash 注入 `search_keyword` 属性，最终由 DEV-4-3 完成 `__init__` 初始化并清理占位。
- **回顾评价**：三模块协作边界清晰，未发生代码冲突，Code Reviewer 对此明确肯定（"两并行模块的接口对接完成干净，未发现代码冲突"）。占位策略有效，但轻微增加了代码的临时复杂度，见技术债务部分。

---

### 二、技术债务识别

#### TD-1：`_build_trash_where_clause()` 中 `datetime.now()` 每次调用独立计算（P2，低风险）

- **描述**：`count_trash()` 和 `list_trash()` 各自调用 `_build_trash_where_clause()`，两次 `datetime.now().isoformat()` 之间存在极小时间差（通常 < 1ms）。理论上在极端情况下（某条数据恰好在两次调用间过期），计数与列表数据可能轻微不一致。
- **当前影响**：PM 在 Release Note 的"已知限制"中已披露，实际使用中概率极低，不影响正常功能。
- **消除方向**：将 `now` 作为参数传入 `_build_trash_where_clause(now: str)`，由调用方统一计算一次后传给 `count_trash()` 和 `list_trash()`，保证同一逻辑流程内时间戳一致。

#### TD-2：`#trash-hint` 的 `compose()` 初始文本与 `_refresh_trash()` 更新文本不同步（P2，极低风险）

- **描述**：`TrashScreen.compose()` 中 Static 的初始文本仅含基础操作提示，缺少翻页和搜索提示；`on_mount()` 会立即调用 `_refresh_trash()` 覆盖该文本，用户实际上无法看到旧文本。
- **当前影响**：功能无误，但代码可读性略低（初始声明与运行时状态不一致）。
- **消除方向**：将初始文本与 `_refresh_trash()` 生成的 hint 字符串保持一致，或提取 hint 构建逻辑为独立方法统一调用。

#### TD-3：`_refresh_trash()` 中 hint 字符串拼接方式（P2，可读性）

- **描述**：`hint.update()` 使用了隐式字符串字面量拼接，中间换行不直观。
- **消除方向**：改为显式 `+` 拼接或 f-string 多行写法，提高可读性。

---

### 三、后续建议

#### 优先级高

**建议 1：引入分页状态抽象（PageState 数据类）**

`BacklogApp` 和 `TrashScreen` 各自维护 `self.page`、`self.page_size`、`self._total_count` 三个变量，逻辑高度重复。建议抽取 `PageState(page, page_size, total_count)` 数据类，提供 `next()`、`prev()`、`reset()`、`total_pages` 等方法，两处 Screen 各持有一个实例，消除重复代码并统一边界处理逻辑。

**建议 2：消除 TD-1（now 参数化）**

将 `_build_trash_where_clause` 改为接受外部 `now` 参数，由调用方（`list_trash` 或 `count_trash` 的公共入口）统一计算，确保同一业务操作内时间戳严格一致。改动范围小，收益明确。

#### 优先级中

**建议 3：搜索防抖（Debounce）**

当前搜索通过弹窗提交（用户确认后触发），无实时搜索压力。若未来改为实时输入搜索（Input 组件即时过滤），需引入防抖机制（如 300ms 延迟），避免每次按键都触发 SQL 查询。当前架构可预留接口。

**建议 4：回收站搜索激活态的视觉反馈强化**

Customer 验收报告建议在搜索激活状态下，hint 区域更清晰地显示当前关键字（如 `Filter: "keyword" | Page 1/2`）。目前通过 notify 提示，但 notify 会自动消失；在 hint 常驻显示关键字可提升用户信心，用户始终能确认当前处于过滤状态。

**建议 5：HelpScreen 补充"回收站翻页"说明**

目前 HelpScreen 在 Navigation 区域描述了 `n`/`p`，但未明确说明这两个键在回收站内同样有效。Customer 验收报告提出了此建议，可在 Trash 分区补充一行说明，减少用户误解。

#### 优先级低

**建议 6：大数据量下的搜索性能优化**

当前 `list_trash()` 和 `list()` 的关键字搜索使用 `LIKE '%keyword%'`，无法利用 B-tree 索引，对极大数据量（数万条）可能有感知延迟。PM 和 Tester 均在报告中提及此点。短期内无需处理；若数据量增长到明显延迟时，可考虑：
  - 在 `title`、`description` 列建立 FTS5 全文索引（SQLite 原生支持）
  - 或引入搜索结果缓存（TTL 较短），避免重复 LIKE 查询

---

### 四、总结

v0.2.0 开发周期整体顺利，三项需求均在一轮开发周期内完成，未触发回归。主要成果：

- **架构层面**：后端分页 + `_build_where_clause()` 共享方案为 repository 层建立了可扩展的分页查询范式，后续新增过滤维度只需在两个私有方法中扩展，无需修改调用方。
- **工程层面**：三模块并行开发策略有效，`getattr` 占位协调虽属临时方案，但未留下技术债务（DEV-4-3 已完整清理）。
- **质量层面**：代码审查发现 P1/P2 问题均在阶段 5 修复，测试 75/75 全部通过，客户验收一次通过，整体交付质量良好。
- **技术债务**：遗留 3 项 P2 级别的低风险技术债务（TD-1/2/3），不影响当前版本功能，建议在 v0.2.x 的维护迭代中逐步消除。

---
