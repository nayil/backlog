## [TST-6-1] Repository 层分页与回收站搜索功能测试

- **阶段：** 6
- **状态：** completed
- **时间：** 2026-03-12T10:30:00

### 输入

读取了以下 Developer 日志：
- `.claude/agents/v0.2.0/developer-repository.log.md`（DEV-4-1）：repository.py 新增分页和回收站搜索接口
- `.claude/agents/v0.2.0/developer-app-pagination.log.md`（DEV-4-2、DEV-5-1）：app.py 翻页功能实现及 P1/P2 修复
- `.claude/agents/v0.2.0/developer-app-trash.log.md`（DEV-4-3）：TrashScreen 搜索功能实现

### 输出

**测试文件：** `tests/test_repository.py`

**新增测试类：** `TestPaginationAndCount`（20 个新测试用例，追加在原有测试之后）

#### 测试用例清单

**list() 分页测试：**

| 测试名 | 测试场景 | 预期结果 | 实际结果 |
|--------|----------|----------|----------|
| test_list_with_limit | 5 个 item，limit=2 | 返回 2 个 | PASS |
| test_list_with_offset | 5 个 item，limit=2, offset=2 | 返回第 3-4 个 | PASS |
| test_list_with_limit_exceeding | 5 个 item，limit=100 | 返回全部 5 个 | PASS |
| test_list_without_limit_backward_compat | 5 个 item，无 limit | 返回全部 5 个 | PASS |

**count() 测试：**

| 测试名 | 测试场景 | 预期结果 | 实际结果 |
|--------|----------|----------|----------|
| test_count_all | 3 个 item | count()=3 | PASS |
| test_count_with_status_filter | TODO×2, DONE×1 | count(status=TODO)=2, count(status=DONE)=1 | PASS |
| test_count_with_keyword_filter | 含 login 标题/描述各 1 个 | count(keyword="login")=2 | PASS |
| test_count_excludes_deleted | 2 个 item 删 1 个 | count()=1 | PASS |

**list_trash() 扩展测试：**

| 测试名 | 测试场景 | 预期结果 | 实际结果 |
|--------|----------|----------|----------|
| test_list_trash_with_keyword | 回收站 keyword 匹配 title | 返回 1 个 | PASS |
| test_list_trash_with_keyword_description | 回收站 keyword 匹配 description | 返回 1 个 | PASS |
| test_list_trash_with_keyword_no_match | 无匹配 keyword | 返回空列表 | PASS |
| test_list_trash_with_limit_offset | 5 个回收站 item 分页 | 两页无重叠，各 2 个 | PASS |
| test_list_trash_backward_compat | 无参调用 | 返回全部 2 个 | PASS |

**count_trash() 测试：**

| 测试名 | 测试场景 | 预期结果 | 实际结果 |
|--------|----------|----------|----------|
| test_count_trash_all | 3 个已删 item | count_trash()=3 | PASS |
| test_count_trash_with_keyword | keyword 过滤 | count_trash("login")=2, count_trash("other")=1 | PASS |
| test_count_trash_excludes_non_deleted | 1 个 active + 1 个已删 | count_trash()=1 | PASS |

#### 通过/失败统计

- **总测试数：** 75（原有 55 + 新增 20）
- **通过：** 75
- **失败：** 0
- **覆盖评估：** 完整覆盖 list() 分页、count()、list_trash() keyword+分页、count_trash() 的所有主要场景，包含边界情况（limit 超出总数、无参向后兼容、无 keyword 匹配）

#### 执行命令

```
python -m pytest tests/test_repository.py -v
```

#### 执行结果摘要

```
75 passed in 0.13s
```

所有测试均通过，无失败用例。

**关联 Developer 条目 ID：** DEV-4-1、DEV-4-2、DEV-4-3、DEV-5-1

---
