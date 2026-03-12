## [CR-5-1] 全模块代码审查

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-11T23:15:00

### 输入
审查 DEV-4-1（models）、DEV-4-2（repository）、DEV-4-3（app）、DEV-4-4（migration）四个模块的代码产出。

### 输出

#### P0 问题（必须修复）

1. **[app.py] 状态循环与 transition_status 校验冲突**
   - `NEXT_STATUS` 定义 `DONE -> TODO`，但 `repository.transition_status` 的 `valid_transitions` 中 DONE 只允许转到 IN_PROGRESS。按下 `s` 键在 DONE 状态时会抛出 ValueError。虽然 app 层 catch 了 ValueError 并显示错误通知，用户体验上"循环切换"功能在 DONE 状态下永远会报错，属于功能设计矛盾。
   - **建议：** 将 `NEXT_STATUS[Status.DONE]` 改为 `Status.IN_PROGRESS`，或在 repository 的 valid_transitions 中允许 DONE->TODO。

2. **[app.py] 编辑时通过 update() 直接设置 status，绕过了 transition_status 校验**
   - `action_edit_item` 中 `self.repo.update(item_id, ..., status=result.status)` 直接更新 status 字段，完全绕过了 `transition_status` 的合法性校验。用户可以通过编辑弹窗将状态从 TODO 直接改为 DONE。
   - **建议：** 如果需要强制校验，编辑时应调用 `transition_status`；如果编辑允许任意状态变更则应记录为设计决策，并移除 transition_status 的约束或在文档中说明两种路径的区别。

#### P1 问题（应该修复）

1. **[repository.py] SQL 注入风险低但 f-string 拼接 SQL 不规范**
   - `update()` 方法中 `f"UPDATE backlog_items SET {', '.join(updates)} WHERE id = ?"` 使用 f-string 拼接列名。虽然列名来自 `allowed` 白名单不会被注入，但这种模式不推荐。当前实现安全，但如果未来 allowed 集合被外部输入影响则存在风险。
   - **建议：** 可保持现状但添加注释说明安全性依赖于 allowed 白名单。

2. **[migration.py] 迁移时 title 可为空字符串**
   - `_convert_task` 中 `title=task.get("title", "")` 允许空标题，但数据库 schema 中 title 是 NOT NULL（不禁止空串）。如果旧数据缺少 title 字段，会创建无标题的 item。
   - **建议：** 添加校验，如 title 为空则跳过或使用默认值如 "Untitled"。

3. **[migration.py] 旧状态 "in_progress" 未映射**
   - `_STATUS_MAP` 只映射了 `pending` 和 `completed`。如果旧数据有 `in_progress` 状态，不会匹配任何 key，fallback 到 `Status.TODO`，导致进行中的任务被错误地标记为 TODO。
   - **建议：** 添加 `"in_progress": Status.IN_PROGRESS` 到映射表。

4. **[repository.py] 缺少上下文管理器支持**
   - `BacklogRepository` 没有实现 `__enter__` / `__exit__`，调用者需要手动调用 `close()`。migration.py 用 try/finally 处理了，但 app.py 没有——应用退出时数据库连接不会被显式关闭。
   - **建议：** 实现 `__enter__`/`__exit__` 协议，或在 app.py 的退出逻辑中调用 `repo.close()`。

5. **[models.py] `from_dict` 对无效枚举值会抛异常**
   - `Status(data["status"])` 如果 data 中 status 值不是合法枚举值（如拼写错误），会抛 ValueError 且没有 fallback。migration.py 中 priority 做了 try/except 处理，但 models.py 的 from_dict 没有。
   - **建议：** 添加 try/except 或文档说明调用者需处理异常。

#### P2 问题（建议改进）

1. **[repository.py/app.py] import 路径使用相对模块名**
   - `from models import ...` 和 `from repository import ...` 依赖 sys.path 操作（app.py 第 26 行）。建议改为包内相对导入或统一使用项目包结构。

2. **[models.py] `datetime.now()` 不含时区信息**
   - 使用 naive datetime，在跨时区场景下可能产生歧义。对本地工具来说可接受，但记录为技术债务。

3. **[app.py] 删除操作无确认弹窗**
   - 按 `d` 直接删除无二次确认，误操作风险较高。

4. **[migration.py] 缺少幂等性保障**
   - 多次运行迁移会重复插入数据。建议添加检查（如目标库已有数据则跳过或提示）。

#### 整体评估

**需修改** — 存在 2 个 P0 问题需要解决（状态循环逻辑冲突、编辑绕过状态校验），3 个 P1 问题建议修复。代码整体结构清晰、模块划分合理、接口一致性好。修复 P0 后可通过。

#### 关联条目
- DEV-4-1（models）、DEV-4-2（repository）、DEV-4-3（app）、DEV-4-4（migration）

---
