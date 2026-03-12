
## [TST-6-1] 软删除与回收站功能测试

- **阶段：** 6
- **状态：** completed
- **时间：** 2026-03-12T02:00:00

### 输入

读取 `developer-core.log.md`（DEV-4-1、DEV-5-1）和 `developer-ui.log.md`（DEV-4-2），了解软删除数据层实现和 TUI 层改动，对 models.py 和 repository.py 的新功能编写测试。

### 输出

#### 测试用例清单

**test_models.py — TestBacklogItemSoftDeleteFields（13 个用例）**

| 测试名称 | 预期结果 | 实际结果 |
|---------|---------|---------|
| test_defaults_deleted_at_none | deleted_at 默认为 None | PASSED |
| test_defaults_expires_at_none | expires_at 默认为 None | PASSED |
| test_to_dict_includes_deleted_at_none | to_dict() 含 deleted_at 键，值为 None | PASSED |
| test_to_dict_includes_expires_at_none | to_dict() 含 expires_at 键，值为 None | PASSED |
| test_to_dict_deleted_at_iso_string | deleted_at 序列化为 ISO 字符串 | PASSED |
| test_to_dict_expires_at_iso_string | expires_at 序列化为 ISO 字符串 | PASSED |
| test_from_dict_parses_deleted_at | from_dict() 正确解析 deleted_at | PASSED |
| test_from_dict_parses_expires_at | from_dict() 正确解析 expires_at | PASSED |
| test_from_dict_missing_deleted_at_defaults_none | 缺少 deleted_at 时返回 None | PASSED |
| test_from_dict_missing_expires_at_defaults_none | 缺少 expires_at 时返回 None | PASSED |
| test_from_dict_null_deleted_at | deleted_at=None 时返回 None | PASSED |
| test_from_dict_null_expires_at | expires_at=None 时返回 None | PASSED |
| test_roundtrip_with_soft_delete_fields | 含软删除字段的完整序列化/反序列化 | PASSED |

**test_repository.py — TestSoftDeleteAndTrash（29 个用例）**

| 测试名称 | 预期结果 | 实际结果 |
|---------|---------|---------|
| test_delete_returns_true | delete() 返回 True | PASSED |
| test_delete_makes_get_return_none | 软删除后 get() 返回 None | PASSED |
| test_delete_item_retrievable_with_include_deleted | get(include_deleted=True) 仍可获取 | PASSED |
| test_delete_sets_deleted_at | deleted_at 被设置 | PASSED |
| test_delete_sets_expires_at_180_days | expires_at 比 deleted_at 晚 180 天 | PASSED |
| test_delete_nonexistent_returns_false | delete(999) 返回 False | PASSED |
| test_delete_already_deleted_returns_false | 重复删除返回 False | PASSED |
| test_list_excludes_deleted | list() 不含已删除记录 | PASSED |
| test_list_empty_after_all_deleted | 全部删除后 list() 为空 | PASSED |
| test_list_trash_returns_deleted_items | list_trash() 返回已删除条目 | PASSED |
| test_list_trash_empty_when_nothing_deleted | 无删除时 list_trash() 为空 | PASSED |
| test_list_trash_excludes_expired | list_trash() 不含已过期条目 | PASSED |
| test_list_trash_newest_first | list_trash() 按 deleted_at 降序排列 | PASSED |
| test_restore_returns_item | restore() 返回恢复后的 BacklogItem | PASSED |
| test_restore_clears_deleted_at | restore() 后 deleted_at 为 None | PASSED |
| test_restore_clears_expires_at | restore() 后 expires_at 为 None | PASSED |
| test_restore_item_appears_in_list | restore() 后 list() 包含该条目 | PASSED |
| test_restore_nonexistent_returns_none | restore(999) 返回 None | PASSED |
| test_restore_non_deleted_returns_none | 对未删除条目 restore() 返回 None | PASSED |
| test_hard_delete_returns_true | hard_delete() 返回 True | PASSED |
| test_hard_delete_removes_record_permanently | hard_delete() 后 get(include_deleted=True) 为 None | PASSED |
| test_hard_delete_nonexistent_returns_false | hard_delete(999) 返回 False | PASSED |
| test_hard_delete_soft_deleted_item | 对软删除条目 hard_delete() 成功 | PASSED |
| test_purge_expired_removes_past_expires | _purge_expired() 清理过期记录 | PASSED |
| test_purge_expired_keeps_future_expires | _purge_expired() 保留未过期记录 | PASSED |
| test_migrate_schema_idempotent | _migrate_schema() 重复调用不报错 | PASSED |
| test_get_categories_excludes_deleted | get_categories() 不含已删除条目的分类 | PASSED |
| test_get_stats_excludes_deleted | get_stats() total 不含已删除条目 | PASSED |
| test_get_stats_with_category_excludes_deleted | get_stats(category) 不含已删除条目 | PASSED |

#### 通过/失败统计

- **新增测试：** 42 个（13 个 models + 29 个 repository）
- **通过：** 42 / 42
- **失败：** 0
- **全量测试（含原有）：** 148 通过，0 失败

#### 测试覆盖评估

- **models.py**：新字段默认值、序列化、反序列化、向后兼容（缺失键/null 值）全部覆盖
- **repository.py**：
  - `get(include_deleted)` ✓
  - `list()` 软删除过滤 ✓
  - `list_trash()` 含过期过滤、排序 ✓
  - `restore()` 正常路径 + 边界（不存在、未删除）✓
  - `hard_delete()` 正常路径 + 边界（不存在、已软删除）✓
  - `_purge_expired()` 清理过期 + 保留未过期 ✓
  - `_migrate_schema()` 幂等性 ✓
  - `get_categories()` 排除已删除 ✓
  - `get_stats()` 排除已删除（含 category 过滤）✓

#### 关联 Developer 条目

- DEV-4-1（数据层软删除实现）
- DEV-5-1（P1-3 list_trash 过期过滤修复已被测试覆盖）

---

## [TST-6-2] HelpScreen 与快捷键绑定测试

- **阶段：** 6
- **状态：** completed
- **时间：** 2026-03-12T10:45:00

### 输入

读取 `developer-ui.log.md`（DEV-4-3），了解 HelpScreen 新增实现和 BacklogApp `?` 快捷键绑定，对 `src/app.py` 中的新增内容进行功能验证。

### 输出

#### 测试用例清单

**功能验证（import + 反射检查）**

| 验证项 | 预期结果 | 实际结果 |
|--------|---------|---------|
| `HelpScreen` 可从 `src.app` 导入 | 导入成功，无异常 | PASSED |
| `BacklogApp.BINDINGS` 包含 `action=help` 的绑定 | 找到 `question_mark` → `help` 绑定 | PASSED |
| `BacklogApp` 拥有 `action_help` 方法 | `hasattr` 返回 True | PASSED |

**现有测试套件（全量回归）**

| 测试文件 | 用例数 | 通过 | 失败 |
|---------|--------|------|------|
| tests/test_migration.py | 18 | 18 | 0 |
| tests/test_models.py | 28 | 28 | 0 |
| tests/test_repository.py | 76 | 76 | 0 |
| tests/test_task_manager.py | 26 | 26 | 0 |
| **合计** | **148** | **148** | **0** |

#### 通过/失败统计

- **功能验证：** 3 / 3 通过
- **全量回归测试：** 148 / 148 通过，0 失败

#### 测试覆盖评估

- `HelpScreen` 类存在且可正常导入 ✓
- `BacklogApp.BINDINGS` 中 `question_mark` → `help` 绑定存在 ✓
- `BacklogApp.action_help` 方法存在 ✓
- 新功能未破坏现有任何测试 ✓
- HelpScreen 中的 `q`/`Escape` 绑定作用域限于 ModalScreen，不影响主界面（由代码审查已确认，功能逻辑无需运行时 TUI 环境验证）

#### 关联 Developer 条目

- DEV-4-3（HelpScreen + `?` 快捷键绑定实现）

---
