## [TL-2-1] Backlog 管理工具技术方案设计

- **阶段：** 2
- **状态：** completed
- **时间：** 2026-03-11T22:30:00

### 输入
需求：将现有的 Python 任务管理器（`src/task_manager.py`）改造为 TUI Backlog 管理工具，支持增删改查、状态流转（Todo → In Progress → Done）、分类管理、搜索过滤、分类统计。数据本地存储，可本地运行。

### 输出

#### 一、现有代码分析

当前项目结构：
- `src/task_manager.py` — 基于全局变量的任务管理模块，支持增删改查、搜索、JSON 持久化
- `tests/test_task_manager.py` — unittest 测试用例，覆盖较全
- 状态仅有 `pending` / `completed`，缺少 `in_progress`
- 无分类（category）功能
- 无 TUI 界面，仅命令行脚本
- 使用全局变量，不利于扩展

#### 二、技术方案概述

| 维度 | 选型 | 理由 |
|------|------|------|
| **TUI 框架** | **Textual** | 基于 Rich，API 现代，支持 CSS 样式，组件丰富（DataTable、Input、Select），开发效率高。curses 过于底层。 |
| **数据存储** | **SQLite** | 比 JSON 更适合查询过滤和统计，支持事务，单文件部署，Python 内置 sqlite3 无额外依赖。 |
| **ORM/数据层** | **直接 sqlite3** | 项目规模小，无需引入 SQLAlchemy，减少依赖。封装一个简单的 Repository 层即可。 |
| **Python 版本** | **3.10+** | Textual 要求 3.8+，选 3.10+ 可用 match/case 和更好的类型提示。 |

依赖清单：`textual>=0.50.0`（唯一外部依赖）

#### 三、模块划分

##### 模块 1：数据模型层（model）
- **文件：** `src/models.py`
- **职责：** 定义 Backlog Item 数据结构（dataclass），包含字段：id, title, description, status(todo/in_progress/done), category, priority, created_at, updated_at
- **接口：**
  - `BacklogItem` dataclass，含 `to_dict()` / `from_dict()` 方法
  - `Status` 枚举：`TODO`, `IN_PROGRESS`, `DONE`
  - `Priority` 枚举：`HIGH`, `MEDIUM`, `LOW`
- **依赖：** 无

##### 模块 2：数据存储层（repository）
- **文件：** `src/repository.py`
- **职责：** SQLite CRUD 操作，表结构管理，查询过滤
- **接口：**
  - `BacklogRepository(db_path: str)`
  - `create(item: BacklogItem) -> BacklogItem`
  - `get(item_id: int) -> Optional[BacklogItem]`
  - `list(status: Optional[Status], category: Optional[str], keyword: Optional[str]) -> List[BacklogItem]`
  - `update(item_id: int, **fields) -> Optional[BacklogItem]`
  - `delete(item_id: int) -> bool`
  - `transition_status(item_id: int, new_status: Status) -> Optional[BacklogItem]`（含状态流转校验：Todo→InProgress→Done，也允许回退）
  - `get_categories() -> List[str]`
  - `get_stats(category: Optional[str]) -> Dict`（按状态统计，可按分类过滤）
- **依赖：** model

##### 模块 3：TUI 界面层（app）
- **文件：** `src/app.py`
- **职责：** Textual 应用主界面，包含列表视图、表单、筛选栏、统计面板
- **子组件：**
  - `BacklogApp(App)` — 主应用
  - `BacklogTable` — DataTable 展示 backlog 列表，支持排序
  - `ItemForm` — 新建/编辑表单（弹窗）
  - `FilterBar` — 状态/分类/关键词筛选
  - `StatsPanel` — 分类统计展示
- **接口：** 无对外 API，作为入口运行
- **依赖：** model, repository, textual

##### 模块 4：迁移兼容层（migration）
- **文件：** `src/migration.py`
- **职责：** 将旧 `tasks.json` 数据迁移到新 SQLite 数据库，字段映射（pending→todo, completed→done）
- **接口：**
  - `migrate_json_to_sqlite(json_path: str, db_path: str) -> int`（返回迁移条数）
- **依赖：** model, repository

#### 四、开发计划

| 顺序 | 模块 | 依赖 | 可并行 |
|------|------|------|--------|
| 1 | model（数据模型） | 无 | 可与其他无依赖模块并行 |
| 2 | repository（数据存储） | model | model 完成后开始 |
| 3 | app（TUI 界面） | model, repository | repository 完成后开始 |
| 4 | migration（迁移） | model, repository | 可与 app 并行 |

**并行策略：**
- model 先行（无依赖，其他模块都依赖它）
- repository 在 model 之后
- app 和 migration 可并行开发（都依赖 model + repository）

#### 五、技术风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| Textual 未安装 | 阻塞 TUI 开发 | 在 `requirements.txt` 中声明，提供 `pip install` 指引 |
| 旧测试需适配 | 现有测试基于全局变量模式 | 保留旧 `task_manager.py` 兼容，新测试针对 repository 层编写 |
| 状态流转逻辑复杂化 | 3 态比 2 态复杂 | 在 repository 层统一校验，不在 UI 层处理 |
| SQLite 并发 | TUI 单进程，风险低 | 单连接即可，无需连接池 |

#### 六、文件结构规划

```
src/
├── models.py          # 模块1：数据模型
├── repository.py      # 模块2：数据存储
├── app.py             # 模块3：TUI 界面
├── migration.py       # 模块4：迁移兼容
├── task_manager.py    # 保留旧代码兼容
tests/
├── test_models.py
├── test_repository.py
├── test_app.py
├── test_migration.py
├── test_task_manager.py  # 保留
requirements.txt           # textual>=0.50.0
```

---

## [TL-7-1] 技术总结报告

- **阶段：** 7
- **状态：** completed
- **时间：** 2026-03-11T23:55:00

### 输入
读取所有 Agent 日志，输出项目技术总结。

### 输出

#### 一、架构决策回顾

| 决策 | 选择 | 回顾评价 |
|------|------|----------|
| TUI 框架 | Textual（替代 curses） | 正确。DataTable、ModalScreen、Select 等组件大幅降低了 UI 开发量，约 280 行即完成全部交互。PM 最初建议 curses，经评估后同意 Textual，决策过程合理。 |
| 数据存储 | SQLite（替代 JSON） | 正确。筛选、统计等功能直接受益于 SQL 查询能力，避免了在 Python 侧手写过滤逻辑。使用内置 sqlite3，未引入额外依赖。 |
| 模块划分 | model → repository → app / migration | 合理。四模块职责清晰，接口边界明确。model 和 repository 的分离使测试可独立于 UI 进行（106 个测试全部使用 `:memory:` 数据库）。app 和 migration 并行开发策略有效。 |
| 状态流转校验层级 | 统一在 repository 层 | 正确。避免了 UI 层和数据层的校验不一致。代码审查阶段发现 app 层存在绕过校验的路径（P0-2），已修复。 |
| 旧代码兼容 | 保留 task_manager.py，新增迁移层 | 稳妥。旧的 44 个测试全部继续通过，新旧代码互不干扰。 |

#### 二、代码审查中发现并修复的关键问题

CodeReviewer（CR-5-1）发现 2 个 P0 和 5 个 P1 问题，Developer（DEV-5-1）全部修复：

**P0 问题（已修复）：**
1. **状态循环与 transition_status 冲突** — app.py 中 DONE 的下一状态定义为 TODO，但 repository 不允许 DONE→TODO。修复：改为 DONE→IN_PROGRESS。
2. **编辑表单绕过状态校验** — update() 直接设置 status 字段，跳过 transition_status 校验。修复：编辑时 status 变更走 transition_status 路径。

**P1 问题（已修复）：**
1. SQL 拼接安全性注释补充
2. 迁移层空标题 fallback 为 "Untitled"
3. 迁移层补充 in_progress 状态映射
4. BacklogRepository 实现上下文管理器协议
5. from_dict 枚举值容错（_safe_enum 方法）

#### 三、技术债务清单

| # | 项目 | 严重度 | 说明 |
|---|------|--------|------|
| TD-1 | datetime 无时区信息 | 低 | models.py 使用 naive datetime，跨时区场景下可能产生歧义。本地工具暂可接受。 |
| TD-2 | 删除操作无确认 | 低 | 按 `d` 直接删除，无二次确认弹窗，存在误操作风险。 |
| TD-3 | 迁移缺少幂等性 | 低 | 多次运行 migration 会重复插入数据，应增加去重或提示机制。 |
| TD-4 | import 路径依赖 sys.path | 低 | app.py 通过 sys.path 操作解决模块导入，未使用标准包结构。项目规模扩大后应改为包内相对导入。 |
| TD-5 | TUI 层缺少自动化测试 | 中 | test_app.py 未编写。Textual 提供了 pilot 测试框架，后续应补充 UI 交互测试。 |
| TD-6 | app 退出时数据库连接关闭 | 低 | 虽已实现上下文管理器，但 app.py 入口处是否使用 with 语句需确认。 |

#### 四、后续改进建议

1. **补充 TUI 测试** — 使用 Textual 的 `App.run_test()` / pilot 框架编写 app.py 的交互测试，覆盖快捷键操作、表单提交、筛选等流程。
2. **包结构规范化** — 将 `src/` 改为 Python 包（添加 `__init__.py`），使用相对导入，消除 sys.path hack。
3. **迁移幂等性** — 迁移前检查目标数据库是否已有数据，给出提示或跳过已迁移记录。
4. **删除确认弹窗** — 在 app.py 中增加删除前的 ModalScreen 确认，防止误操作。
5. **时区感知** — 将 `datetime.now()` 改为 `datetime.now(timezone.utc)`，统一使用 UTC 存储。
6. **配置外化** — 数据库路径当前硬编码为 `~/.backlog/backlog.db`，可改为命令行参数或配置文件。
7. **CI 集成** — 添加 pytest + coverage 的 CI 配置，确保 106 个测试持续通过。

---

## [TL-2-2] 修复 Select.NULL 导致的 ProgrammingError

- **阶段：** 2
- **状态：** completed
- **时间：** 2026-03-11T00:00:00Z

### 输入
运行时报错：`ProgrammingError: Error binding parameter 1: type 'NoSelection' is not supported`。根本原因是 `Select.Changed` 事件的 `event.value` 可能为 `Select.BLANK`（Textual 的 NoSelection 哨兵对象），未被过滤就传入了 SQLite 查询。

### 输出

#### 受影响位置

**文件：** `/root/yanay/codes/multi-agents-demo/src/app.py`

| 位置 | 方法 | 行号 | 问题 |
|------|------|------|------|
| 1 | `on_status_filter` | 328-331 | `event.value` 为 `Select.BLANK` 时，`val == "all"` 为 False，执行 `Status(val)` 抛异常或传入非法值 |
| 2 | `on_category_filter` | 334-337 | `event.value` 为 `Select.BLANK` 时，`val == "all"` 为 False，非法值被赋给 `self.filter_category` 并传入 SQL |

#### 修复方案

在两个 handler 中增加对 `Select.BLANK` 的检查，将其视同 `"all"`（即清除筛选条件）。

**修改 1 — `on_status_filter`（第 328-331 行）：**

```python
@on(Select.Changed, "#sel-filter-status")
def on_status_filter(self, event: Select.Changed) -> None:
    val = event.value
    if val == Select.BLANK or val == "all":
        self.filter_status = None
    else:
        self.filter_status = Status(val)
    self._refresh_table()
```

**修改 2 — `on_category_filter`（第 334-337 行）：**

```python
@on(Select.Changed, "#sel-filter-category")
def on_category_filter(self, event: Select.Changed) -> None:
    val = event.value
    if val == Select.BLANK or val == "all":
        self.filter_category = None
    else:
        self.filter_category = val
    self._refresh_table()
```

#### 说明
- `Select.BLANK` 是 Textual 中表示"未选择"的哨兵值（某些版本中为 `Select.NULL`，视 Textual 版本而定；建议同时检查 `Select.BLANK`，或使用 `isinstance` 判断非字符串值）。
- 更健壮的写法也可以是：`if not isinstance(val, str):` 来拦截所有非字符串哨兵。
- 两处修改逻辑完全对称，无其他受影响位置（表单中的 Select 使用固定初始值，不会出现 BLANK）。

---
