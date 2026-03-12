## [TST-6-1] 测试验证

- **阶段：** 6
- **状态：** completed
- **时间：** 2026-03-12T11:30:00

### 输入
DEV-4-1 和 DEV-5-1 的代码产出（三处改动：状态保存 Bug 修复、Age 列、VersionScreen + `v` 快捷键）

### 输出

#### 测试用例清单

**A. 单元测试（`test_changes.py`）— 28 个用例**

| 测试类 | 测试方法 | 预期结果 | 实际结果 |
|---|---|---|---|
| TestAgeCalculation | test_age_zero_days | created_at=now → "0d" | ✅ 通过 |
| TestAgeCalculation | test_age_five_days | 5天前 → "5d" | ✅ 通过 |
| TestAgeCalculation | test_age_thirty_days | 30天前 → "30d" | ✅ 通过 |
| TestAgeCalculation | test_age_none_guard | created_at=None → "-" | ✅ 通过 |
| TestAgeCalculation | test_backlog_item_none_created_at | BacklogItem.created_at=None → "-" | ✅ 通过 |
| TestAgeCalculation | test_backlog_item_with_created_at | BacklogItem 7天前 → "7d" | ✅ 通过 |
| TestVersionParsing | test_no_release_dir | 不存在目录 → [] | ✅ 通过 |
| TestVersionParsing | test_empty_release_dir | 空目录 → [] | ✅ 通过 |
| TestVersionParsing | test_single_version_file | 单文件提取版本 → ["v0.1.0"] | ✅ 通过 |
| TestVersionParsing | test_multiple_versions_sorted_descending | 多版本降序排列 → ["v0.2.0","v0.1.1","v0.1.0"] | ✅ 通过 |
| TestVersionParsing | test_deduplication | 同版本多文件去重 → ["v0.1.0"] | ✅ 通过 |
| TestVersionParsing | test_non_version_files_ignored | 无版本文件忽略 → ["v1.2.3"] | ✅ 通过 |
| TestVersionParsing | test_semantic_sort_major_version | major 差异排序 → ["v2.0.0","v1.0.0","v0.9.9"] | ✅ 通过 |
| TestStatusBugFix | test_original_status_snapshot_differs_from_mutated | 捕获快照后可检测变化 | ✅ 通过 |
| TestStatusBugFix | test_original_status_no_change_detected_correctly | 未变化时快照比较返回相等 | ✅ 通过 |
| TestStatusBugFix | test_without_snapshot_bug_would_occur | 无快照时同对象比较永远相等（证明原 Bug） | ✅ 通过 |
| TestStatusBugFix | test_status_enum_values | Status 枚举值互不相等 | ✅ 通过 |
| TestStaticCodeChecks | test_original_status_defined_before_push_screen | original_status 和比较语句均存在 | ✅ 通过 |
| TestStaticCodeChecks | test_original_status_before_push_screen_ordering | original_status 赋值在 push_screen 之前 | ✅ 通过 |
| TestStaticCodeChecks | test_age_column_in_add_columns | add_columns 包含 "Age" | ✅ 通过 |
| TestStaticCodeChecks | test_age_str_logic_present | age_str 和 item.created_at 存在 | ✅ 通过 |
| TestStaticCodeChecks | test_version_screen_class_exists | class VersionScreen 存在 | ✅ 通过 |
| TestStaticCodeChecks | test_v_binding_present | "v", "show_versions" 绑定存在 | ✅ 通过 |
| TestStaticCodeChecks | test_action_show_versions_exists | action_show_versions 方法存在 | ✅ 通过 |
| TestStaticCodeChecks | test_parse_versions_method_exists | _parse_versions 方法存在 | ✅ 通过 |
| TestStaticCodeChecks | test_get_release_dir_uses_file_not_cwd | _get_release_dir 使用 __file__ 而非 CWD | ✅ 通过 |
| TestStaticCodeChecks | test_help_screen_v_key_documentation | HelpScreen 包含 "Show version history" | ✅ 通过 |
| TestStaticCodeChecks | test_datetime_now_outside_loop | now = datetime.now() 在 for 循环外 | ✅ 通过 |

**B. 导入测试**

```
$ cd .worktrees/v0.2.0 && python -c "from src.app import BacklogApp, VersionScreen; print('Import OK')"
Import OK
```

结果：✅ 通过，无语法错误

#### 通过/失败统计

| 类别 | 总计 | 通过 | 失败 |
|---|---|---|---|
| 单元测试 | 28 | 28 | 0 |
| 导入测试 | 1 | 1 | 0 |
| **合计** | **29** | **29** | **0** |

#### 失败用例详情

无失败用例。

#### 测试覆盖评估

| 改动 | 覆盖维度 | 覆盖状态 |
|---|---|---|
| **改动 A（状态 Bug 修复）** | 正常检测变化、无变化检测、证明原 Bug 逻辑、枚举值正确性 | ✅ 完整覆盖 |
| **改动 B（Age 列）** | 0天/5天/30天、None 守卫、BacklogItem 对象、静态检查列定义与循环外 now | ✅ 完整覆盖 |
| **改动 C（VersionScreen + v 键）** | 空目录/单版本/多版本/去重/忽略无关文件/语义排序、类与方法存在性、__file__ 定位、v 键绑定、HelpScreen 说明 | ✅ 完整覆盖 |
| **DEV-5-1 P1 修复（HelpScreen v 键说明）** | "Show version history" 存在性检查 | ✅ 覆盖 |
| **DEV-5-1 P2 修复（now 提取到循环外）** | datetime.now() 在 for 循环前的位置检查 | ✅ 覆盖 |

#### 关联的 Developer 条目 ID

- DEV-4-1（三项功能改动）
- DEV-5-1（P1/P2 修复）

---
