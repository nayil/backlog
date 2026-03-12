## [PM-2-1] 项目计划 v0.2.0

- **阶段：** 2
- **状态：** completed
- **时间：** 2026-03-12T10:00:00Z

### 输入

需求描述：
1. 修复 log 状态变更保存后不生效问题
2. 展示每条 log 自创建日期起至当前时间经过的天数
3. 在 UI 中展示历史版本列表（从 `release/` 目录下的文件名推断版本信息）

历史版本推断（来自 `release/` 目录）：
- `backlog-manager-v0.1.0-用户手册.md` → v0.1.0
- `backlog-manager-v0.2.0-用户手册.md` → v0.2.0（含中文版和英文版：`backlog-manager-v0.2.0-user-manual.md`）

TechLeader 日志：本阶段并行工作，文件尚未生成，基于需求直接规划。

### 输出

#### 当前版本号

**v0.2.0**（在 v0.1.0 基础上递增 minor，包含功能新增和 Bug 修复）

---

#### 里程碑清单

| # | 里程碑 | 预期完成条件 |
|---|--------|------------|
| M1 | **Bug 修复：状态变更持久化** | log 状态字段在保存操作后能正确写入存储层，刷新页面/重新加载后状态一致 |
| M2 | **功能：天数展示** | 每条 log 条目 UI 中展示"距今 N 天"或"创建 N 天前"字样，计算逻辑基于创建日期与当前日期的差值 |
| M3 | **功能：历史版本列表** | UI 中有专属入口展示版本列表，版本号从 `release/` 目录文件名解析；列表可访问对应 release 文档 |
| M4 | **集成测试 & 验收** | 三项需求全部通过 Tester 测试；Customer Agent 验收通过 |

**预期交付顺序：** M1 → M2 → M3 → M4（M1 为阻塞项，M2/M3 可并行开发）

---

#### 风险清单

| 优先级 | 风险项 | 影响 | 应对策略 |
|--------|--------|------|---------|
| P0 | **状态持久化 Bug 根因不明**：需定位是 UI 未触发保存、存储层未更新，还是读取时未刷新状态 | 可能导致修复方向错误，返工成本高 | TechLeader 优先完成根因分析，再派发 Developer |
| P1 | **`release/` 目录解析脆弱性**：文件命名不规范或新增文件时格式变化，导致版本解析失败 | 版本列表功能不可用或显示错误 | 定义严格的正则解析规则，增加兜底逻辑（解析失败时展示原始文件名） |
| P1 | **天数计算时区问题**：服务端/客户端时区不一致导致天数偏差 | 展示值与用户预期不符 | 统一使用 UTC 或本地时区，在 TL 技术方案中明确约定 |
| P2 | **历史版本文件数量增长**：`release/` 目录文件增多后列表过长 | 用户体验下降 | 建议按版本号降序展示，考虑分页或折叠旧版本 |

---

#### 可行性评估

- **Bug 修复（M1）**：可行性高。状态变更持久化属于典型的数据流问题，代码定位范围清晰（保存函数、存储接口、状态读取）。预计 1 个开发迭代可解决。
- **天数展示（M2）**：可行性高。纯前端/展示层改动，无复杂业务逻辑。创建日期字段已存在（v0.1.0 功能），只需添加计算和渲染逻辑。
- **历史版本列表（M3）**：可行性中等。依赖对 `release/` 目录的读取能力（文件系统或静态资源列举）。需确认当前架构是否支持动态读取目录，若为纯静态部署需额外方案。

**整体可行性：高**，三项需求均为增量改动，不涉及架构重构。

---

#### 总体建议

1. **优先解决 M1（状态 Bug）**，此问题影响数据准确性，属于质量问题，需第一优先级处理。
2. **M2 和 M3 可并行派发 Developer**（如 TechLeader 确认无依赖关系），缩短交付周期。
3. **历史版本解析方案需 TechLeader 明确**：确认是服务端读目录、构建时静态生成列表，还是前端动态获取，影响 M3 的实现复杂度。
4. 建议 Tester 重点覆盖：状态保存前后的数据一致性断言、天数计算的边界值（同日创建=0天、跨月/跨年）、版本解析的正则鲁棒性。
5. 本版本发布后，`release/` 目录将新增 `backlog-manager-v0.2.0-*.md`，版本列表功能会自然包含自身，形成闭环验证。

---

## [PM-3-1] 计划对齐评估

- **阶段：** 3
- **状态：** completed
- **时间：** 2026-03-12T10:30:00Z

### 输入

TechLeader 日志（TL-2-1）技术方案摘要：

1. **Bug 修复（模块 A）**：定位到 `action_edit_item` 中的闭包引用陷阱——`ItemFormScreen.action_submit` 直接修改 `self.item` 对象字段后调用 `dismiss(self.item)`，导致回调中 `result` 和 `item` 是同一个对象，`result.status != item.status` 永远为 `False`，`transition_status` 从不执行。修复方案：在 `push_screen` 前记录 `original_status = item.status` 快照，与 `result.status` 比较。
2. **Age 列（模块 B）**：在 `on_mount` 的列定义新增 `"Age"`，在 `_refresh_table` 每行追加 `(datetime.now() - item.created_at).days` 计算结果，`created_at` 为 None 时显示 `"-"`。
3. **VersionScreen（模块 C）**：新增 `VersionScreen(ModalScreen)` 类，使用 `Path(__file__).resolve().parent.parent / "release"` 定位 `release/` 目录，正则提取版本号并排序展示；`BacklogApp` 新增 `v` 快捷键触发。
4. **开发策略**：三模块均集中在 `src/app.py`，建议单一 Developer 顺序实现（A → B → C）避免合并冲突。

### 输出

#### 可行性评估结论

**整体评估：可行，方案正确，计划确认。**

| 模块 | 评估结论 | 说明 |
|------|---------|------|
| **A. Bug 修复（闭包陷阱）** | ✅ 正确 | 经人工核查代码（`app.py` 第 154-162 行 `action_submit`，第 691 行 `result.status != item.status`），根因分析与代码实际完全吻合。快照方案（`original_status = item.status`）是最小改动、最安全的修复方式。`transition_status` 的合法性校验约束保持不变，行为一致。 |
| **B. Age 列** | ✅ 可行 | `on_mount` 的列定义（第 575 行）和 `_refresh_table` 的 `add_row`（第 592-599 行）均已确认，改动位置准确。`created_at` 的 None 守卫已纳入方案，`datetime` import 风险已识别（P2，需补充）。 |
| **C. VersionScreen** | ✅ 可行 | `release/` 目录实际存在（含 3 个文件），文件名格式确认符合正则 `v\d+\.\d+\.\d+`。`Path(__file__).resolve().parent.parent` 定位策略在 Textual TUI 环境中稳定可靠（不依赖 CWD）。语义版本降序排序逻辑正确。 |
| **单一 Developer 策略** | ✅ 合理 | 三个模块均在 `src/app.py`，并行开发会引入合并冲突。单一 Developer 顺序实现是合理选择，改动量有限，不会显著增加交付时间。 |

#### 需要 TechLeader 调整的问题

**无需调整。** 技术方案完整、根因分析准确、风险识别到位。

以下两点 TechLeader 已在风险清单中覆盖，Developer 实现时注意即可：

1. **`from datetime import datetime` 的 import 确认**（P2）：Developer 需检查 `app.py` 顶层是否已有，若无则补充。
2. **`release/` 目录不存在时的友好提示**（P1）：`_parse_versions` 返回空列表时，`VersionScreen` 需展示"暂无历史版本"提示，而非空白或崩溃。

#### 总体建议

1. 直接进入阶段 4 并行开发，派发单一 Developer 实现 A → B → C 顺序。
2. Tester 重点验证：状态保存前后一致性（P0 Bug 修复验证）、Age 边界值（same-day = 0d）、版本解析的正则鲁棒性。
3. 计划风险评级与 PM-2-1 评估一致，无新增风险项。

---

## [PM-7-1] 项目完成确认 v0.2.0

- **阶段：** 7
- **状态：** completed
- **时间：** 2026-03-12T09:19:29Z

### 输入

各阶段日志摘要：

- **TechLeader（TL-2-1）**：完成技术调研，定位状态保存 Bug 根因（闭包引用陷阱），设计 Age 列和 VersionScreen 方案，三模块均集中在 `src/app.py`，建议单一 Developer 顺序实现。状态：completed ✓
- **Developer（DEV-4-1）**：实现三项功能改动（Bug A 修复、Age 列、VersionScreen + `v` 快捷键），导入验证通过。状态：completed ✓
- **Developer（DEV-5-1）**：修复 CR-5-1 审查反馈的 P1 问题（HelpScreen 补充 `v` 键说明）及 P2 问题（`datetime.now()` 提取到循环外）。状态：completed ✓
- **CodeReviewer（CR-5-1）**：首轮审查，无 P0 问题，发现 1 条 P1（HelpScreen 未更新）和 3 条 P2，整体评估通过（建议处理 P1 后发布）。状态：completed ✓
- **CodeReviewer（CR-5-2）**：第二轮审查，P1 和 P2 全部修复确认，无新增问题，整体评估**通过**，可进入测试阶段。状态：completed ✓
- **Tester（TST-6-1）**：编写并执行 29 个测试用例（28 单元 + 1 导入），**全部通过（29/29）**，三项改动测试覆盖完整。状态：completed ✓

### 输出

**版本号：** 0.2.0

**开发状态：** 已全部完成

---

#### 里程碑完成情况

| # | 里程碑 | 状态 |
|---|--------|------|
| M1 | Bug 修复：状态变更持久化 | ✅ 已完成（DEV-4-1，经 CR-5-2 验证） |
| M2 | 功能：天数展示（Age 列） | ✅ 已完成（DEV-4-1，经 TST-6-1 验证） |
| M3 | 功能：历史版本列表（VersionScreen） | ✅ 已完成（DEV-4-1，经 TST-6-1 验证） |
| M4 | 集成测试 & 验收 | ✅ 测试通过 29/29，待 Customer 验收 |

---

#### Release Note v0.2.0

**发布版本：** v0.2.0
**发布日期：** 2026-03-12
**基线版本：** v0.1.0

##### Bug Fixes

- **修复 log 状态变更保存后不生效的问题**（`src/app.py`）
  - 根因：`action_edit_item` 回调中存在闭包引用陷阱——`ItemFormScreen.action_submit` 直接修改传入的 `item` 对象字段并返回同一引用，导致状态比较 `result.status != item.status` 永远为 `False`，`transition_status` 从不执行。
  - 修复：在 `push_screen` 前记录 `original_status = item.status` 快照，回调中与快照而非同一对象比较。

##### New Features

- **新增 Age 列**（`src/app.py`）
  - 在主列表新增 `Age` 展示列，显示每条 log 自创建日期起经过的天数（格式：`Nd`）。
  - `created_at` 为空时展示 `-`，`datetime.now()` 在循环外缓存避免时间漂移。

- **新增历史版本列表（VersionScreen）**（`src/app.py`）
  - 按 `v` 键可弹出版本历史 Modal，列出 `release/` 目录下所有历史版本。
  - 版本号通过正则 `v\d+\.\d+\.\d+` 从文件名提取，去重后按语义版本降序排列。
  - 无版本文件时展示友好提示 `(no releases found)`。
  - 帮助界面（按 `?`）同步更新，新增 `v — Show version history` 说明。

##### Quality Improvements

- `HelpScreen` 补充 `v` 键功能说明，提升功能可发现性。
- `_refresh_table` 中 `datetime.now()` 提取到循环外，语义更清晰，避免微小时间漂移。

##### Test Coverage

- 新增 28 个单元测试，覆盖 Age 计算、版本解析、状态 Bug 修复逻辑及静态代码检查。
- 全部 29 个测试用例通过（28 单元 + 1 导入验证），无失败用例。

---

## [PM-9-1] 项目总结 v0.2.0

- **阶段：** 9
- **状态：** completed
- **时间：** 2026-03-12T12:00:00Z

### 输入

各版本/阶段日志摘要：

- **TL-2-1（TechLeader）**：技术调研完成，定位状态保存 Bug 根因（闭包引用陷阱），设计 Age 列和 VersionScreen 方案，三模块均集中在 `src/app.py`，建议单一 Developer 顺序实现（A → B → C）。状态：completed ✓
- **PM-2-1 / PM-3-1（ProjectManager）**：版本规划 v0.2.0，里程碑 M1-M4 制定完成，技术方案评估通过，计划确认可行。状态：completed ✓
- **DEV-4-1（Developer）**：实现三项功能改动（Bug A 修复、Age 列、VersionScreen + `v` 快捷键），代码导入验证通过。状态：completed ✓
- **DEV-5-1（Developer）**：修复 CR-5-1 审查反馈的 P1 问题（HelpScreen 补充 `v` 键说明）及 P2 问题（`datetime.now()` 提取到循环外）。状态：completed ✓
- **CR-5-1（CodeReviewer）**：首轮审查，无 P0，发现 1 条 P1（HelpScreen 未更新）和 3 条 P2，整体评估通过（建议处理 P1）。状态：completed ✓
- **CR-5-2（CodeReviewer）**：第二轮审查，P1 和 P2 全部修复确认，无新增问题，整体评估**通过**，可进入测试阶段。状态：completed ✓
- **TST-6-1（Tester）**：编写并执行 29 个测试用例（28 单元 + 1 导入），**全部通过（29/29）**，三项改动测试覆盖完整。状态：completed ✓
- **PM-7-1（ProjectManager）**：项目完成确认，里程碑 M1-M4 全部达成，Release Note 已生成。状态：completed ✓
- **CUST-7-1（Customer）**：验收结论**通过**，四项验证均已完成，无未达预期项。状态：completed ✓

### 输出

**最终版本号：** 0.2.0
**项目状态：** 已完成，客户验收通过

---

#### 里程碑达成情况

| # | 里程碑 | 状态 | 备注 |
|---|--------|------|------|
| M1 | Bug 修复：状态变更持久化 | ✅ 已完成 | DEV-4-1 实现，CR-5-2 审查通过，TST-6-1 测试覆盖 |
| M2 | 功能：天数展示（Age 列） | ✅ 已完成 | DEV-4-1 实现，TST-6-1 测试覆盖（6 个用例） |
| M3 | 功能：历史版本列表（VersionScreen） | ✅ 已完成 | DEV-4-1 实现，TST-6-1 测试覆盖（7 个版本解析用例） |
| M4 | 集成测试 & 验收 | ✅ 已完成 | 29/29 测试通过，CUST-7-1 验收通过 |

---

#### 风险回顾

| 风险项 | 初始等级 | 实际结果 |
|--------|---------|---------|
| 状态持久化 Bug 根因定位 | P0 | ✅ 已解决：TL 精确定位为闭包引用陷阱，快照方案最小修复 |
| `release/` 目录路径解析不稳定 | P1 | ✅ 未发生：采用 `__file__` 定位，运行验证稳定 |
| `item.created_at` 为 None 时崩溃 | P1 | ✅ 未发生：Developer 添加了完善的 None 守卫 |
| `DONE→TODO` 状态转换受限 | P1 | ℹ️ 已知约束：保留现有转换规则，Edit 表单在 `ValueError` 时展示通知，行为符合预期 |
| `datetime` 未导入 | P2 | ✅ 已解决：Developer 在 DEV-4-1 中补充了 import |
| HelpScreen 未反映新功能 | P2（升级为P1） | ✅ 已解决：DEV-5-1 修复，CR-5-2 确认 |

---

#### 完整 Release Note

**发布版本：** v0.2.0
**发布日期：** 2026-03-12
**基线版本：** v0.1.0

##### Bug Fixes

- **修复 log 状态变更保存后不生效的问题**（`src/app.py`）
  - 根因：`action_edit_item` 回调中存在闭包引用陷阱——`ItemFormScreen.action_submit` 直接修改传入的 `item` 对象字段并返回同一引用，导致状态比较 `result.status != item.status` 永远为 `False`，`transition_status` 从不执行。
  - 修复：在 `push_screen` 前记录 `original_status = item.status` 快照，回调中与快照而非同一对象比较。

##### New Features

- **新增 Age 列**（`src/app.py`）
  - 在主列表新增 `Age` 展示列，显示每条 log 自创建日期起经过的天数（格式：`Nd`）。
  - `created_at` 为空时展示 `-`，`datetime.now()` 在循环外缓存避免时间漂移。

- **新增历史版本列表（VersionScreen）**（`src/app.py`）
  - 按 `v` 键可弹出版本历史 Modal，列出 `release/` 目录下所有历史版本。
  - 版本号通过正则 `v\d+\.\d+\.\d+` 从文件名提取，去重后按语义版本降序排列。
  - 无版本文件时展示友好提示 `(no releases found)`。
  - 帮助界面（按 `?`）同步更新，新增 `v — Show version history` 说明。

##### Quality Improvements

- `HelpScreen` 补充 `v` 键功能说明，提升功能可发现性。
- `_refresh_table` 中 `datetime.now()` 提取到循环外，语义更清晰，避免微小时间漂移。

##### Test Coverage

- 新增 28 个单元测试，覆盖 Age 计算、版本解析、状态 Bug 修复逻辑及静态代码检查。
- 全部 29 个测试用例通过（28 单元 + 1 导入验证），无失败用例。

---

**产品使用说明书：**
已写入 `./release/backlog-manager-v0.2.0-用户手册.md`

---
