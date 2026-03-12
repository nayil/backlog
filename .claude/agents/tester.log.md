## [TST-6-1] Backlog 管理工具测试验证

- **阶段：** 6
- **状态：** completed
- **时间：** 2026-03-11T23:45:00

### 输入
根据 Developer 日志（DEV-4-1 ~ DEV-4-4、DEV-5-1）的代码产出，为 models、repository、migration 三个模块编写单元测试并执行验证。

### 输出

#### 测试用例清单

**test_models.py（14 个用例）**
| 用例 | 结果 |
|------|------|
| Status 枚举值正确 | PASSED |
| Status 从字符串构造 | PASSED |
| Status 无效值抛异常 | PASSED |
| Priority 枚举值正确 | PASSED |
| Priority 无效值抛异常 | PASSED |
| BacklogItem 默认值 | PASSED |
| to_dict 完整转换 | PASSED |
| from_dict 完整字段 | PASSED |
| from_dict 最小字段 | PASSED |
| from_dict 无效 status 回退 | PASSED |
| from_dict 无效 priority 回退 | PASSED |
| from_dict None status 回退 | PASSED |
| to_dict/from_dict 往返一致 | PASSED |
| to_dict None 时间戳处理 | PASSED |

**test_repository.py（30 个用例）**
| 用例 | 结果 |
|------|------|
| create 分配 ID | PASSED |
| create 多条递增 ID | PASSED |
| get 已有记录 | PASSED |
| get 不存在返回 None | PASSED |
| list 全部 | PASSED |
| list 按状态筛选 | PASSED |
| list 按分类筛选 | PASSED |
| list 按关键词筛选 | PASSED |
| list 空库 | PASSED |
| update 标题 | PASSED |
| update 状态枚举 | PASSED |
| update 优先级枚举 | PASSED |
| update 不存在返回 None | PASSED |
| update 忽略未知字段 | PASSED |
| update 无字段不报错 | PASSED |
| delete 已有记录 | PASSED |
| delete 不存在返回 False | PASSED |
| transition TODO→IN_PROGRESS | PASSED |
| transition IN_PROGRESS→DONE | PASSED |
| transition IN_PROGRESS→TODO | PASSED |
| transition DONE→IN_PROGRESS | PASSED |
| transition 非法 TODO→DONE | PASSED |
| transition 非法 DONE→TODO | PASSED |
| transition 不存在返回 None | PASSED |
| get_categories 正常 | PASSED |
| get_categories 空库 | PASSED |
| get_stats 正常 | PASSED |
| get_stats 按分类过滤 | PASSED |
| get_stats 空库 | PASSED |
| 上下文管理器 | PASSED |

**test_migration.py（18 个用例）**
| 用例 | 结果 |
|------|------|
| 基本转换 | PASSED |
| completed 映射 DONE | PASSED |
| in_progress 映射 | PASSED |
| 未知状态回退 TODO | PASSED |
| 缺失状态回退 TODO | PASSED |
| 无效优先级回退 MEDIUM | PASSED |
| 空分类设默认 | PASSED |
| 缺失分类设默认 | PASSED |
| 已有分类保留 | PASSED |
| 空标题变 Untitled | PASSED |
| 缺失标题变 Untitled | PASSED |
| 空白标题变 Untitled | PASSED |
| 基本迁移 | PASSED |
| 空列表迁移 | PASSED |
| 文件不存在抛异常 | PASSED |
| 无效 JSON 抛异常 | PASSED |
| 非列表 JSON 抛异常 | PASSED |
| 迁移数据可读取验证 | PASSED |

**test_task_manager.py（旧测试，44 个用例）** — 全部 PASSED

#### 统计

| 模块 | 通过 | 失败 | 合计 |
|------|------|------|------|
| test_models | 14 | 0 | 14 |
| test_repository | 30 | 0 | 30 |
| test_migration | 18 | 0 | 18 |
| test_task_manager | 44 | 0 | 44 |
| **总计** | **106** | **0** | **106** |

#### 测试覆盖评估
- models：枚举值、dataclass 默认值、序列化/反序列化、容错回退均已覆盖
- repository：CRUD 全路径、状态流转合法/非法、筛选组合、统计、上下文管理器均已覆盖
- migration：字段映射、边界输入（空/缺失/无效）、文件异常、端到端迁移验证均已覆盖
- 所有测试使用 `:memory:` SQLite 或临时文件，无外部依赖

#### 关联 Developer 条目
DEV-4-1, DEV-4-2, DEV-4-4, DEV-5-1

---

## [TST-6-2] Select.BLANK bug 修复验证及冒烟测试

- **阶段：** 6
- **状态：** completed
- **时间：** 2026-03-11T23:55:00Z

### 输入
验证 DEV-5-2 中 Select.BLANK/NoSelection bug 修复，确认 `on_status_filter` 和 `on_category_filter` 正确处理哨兵值。

### 输出

#### 1. 现有测试套件回归

运行 `python -m pytest tests/ -v`，全部 **106 个用例通过**，无回归。

#### 2. 修复代码逻辑审查

审查 `src/app.py` 第 327-343 行：

- `on_status_filter`：守卫条件 `val == Select.BLANK or not isinstance(val, str) or val == "all"` 正确覆盖三种清除筛选的场景
- `on_category_filter`：对称实现，逻辑一致
- 正常的具体值选择路径未受影响（`Status(val)` 和 `self.filter_category = val`）

**结论：修复逻辑正确。**

#### 3. 集成冒烟测试（10 个用例）

| # | 用例 | 结果 |
|---|------|------|
| 1 | list(None, None, None) 返回全部 5 条 | PASSED |
| 2 | list(status=TODO) 返回 3 条 | PASSED |
| 3 | list(category='frontend') 返回 2 条 | PASSED |
| 4 | list(keyword='Search') 返回 1 条 | PASSED |
| 5 | list(status=TODO, category='backend') 返回 1 条 | PASSED |
| 6 | get_stats(category=None) 统计正确 | PASSED |
| 7 | get_stats(category='frontend') 按分类过滤正确 | PASSED |
| 8 | get_categories 返回预期分类 | PASSED |
| 9 | 上下文管理器正常工作 | PASSED |
| 10 | Select.BLANK 非字符串且非 "all"，守卫条件生效 | PASSED |

#### 统计

| 测试类别 | 通过 | 失败 |
|----------|------|------|
| 回归测试套件 | 106 | 0 |
| 集成冒烟测试 | 10 | 0 |
| **总计** | **116** | **0** |

#### 结论
所有测试通过。Select.BLANK bug 修复有效，未引入回归问题。

#### 关联 Developer 条目
DEV-5-2

---
