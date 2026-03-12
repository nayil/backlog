## [DEV-4-3] 实现 TUI 界面层（app 模块）

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-11T23:00:00

### 输入
根据 TechLeader 技术方案中模块 3 的规格，基于已完成的 models.py 和 repository.py 实现 Textual TUI 界面。

### 输出

#### 改动说明

创建 `src/app.py`，使用 Textual 框架实现完整的 Backlog 管理 TUI 应用。

#### 实现内容

1. **BacklogApp(App)** — 主应用类
   - 数据库路径默认 `~/.backlog/backlog.db`，自动创建目录
   - 顶部 Header 标题栏
   - 底部 Footer 显示快捷键 + 统计栏（各状态数量）
   - 筛选栏：状态筛选 Select + 分类筛选 Select

2. **DataTable 列表视图** — 显示 ID、Title、Status、Category、Priority，行选择模式

3. **快捷键操作**
   - `a` = 添加新 item（弹出 ItemFormScreen）
   - `e` = 编辑选中 item（弹出 ItemFormScreen，预填数据）
   - `d` = 删除选中 item
   - `s` = 状态循环切换（Todo → In Progress → Done → Todo），通过 repository.transition_status 校验合法性
   - `/` = 搜索（弹出 SearchScreen，输入关键词过滤）
   - `q` = 退出

4. **ItemFormScreen(ModalScreen)** — 添加/编辑弹窗
   - 输入项：Title、Description、Category、Priority（Select）
   - 编辑模式额外显示 Status（Select）
   - Ctrl+S 保存，Esc 取消

5. **SearchScreen(ModalScreen)** — 搜索弹窗
   - 输入关键词后 Enter 提交，空字符串清除过滤

6. **筛选功能** — 状态和分类两个 Select 下拉框实时过滤列表

7. **统计栏** — 底部显示 Total / Todo / In Progress / Done 数量

#### 修改的文件
- `src/app.py`（新建，约 280 行）

#### 依赖
- `textual>=0.50.0`
- `src/models.py`（Status, Priority, BacklogItem）
- `src/repository.py`（BacklogRepository）

---

## [DEV-5-1] 修复 CodeReviewer P0/P1 问题

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-11T23:30:00

### 输入
根据 CR-5-1 审查报告，修复 2 个 P0 问题和 5 个 P1 问题。

### 输出

#### 修复清单

**P0-1: DONE 状态 toggle 逻辑冲突**
- 文件：`src/app.py`
- 修复：将 `NEXT_STATUS[Status.DONE]` 从 `Status.TODO` 改为 `Status.IN_PROGRESS`，与 `repository.transition_status` 的 `valid_transitions` 保持一致。

**P0-2: 编辑表单绕过 transition_status 校验**
- 文件：`src/app.py`
- 修复：`action_edit_item` 中将非 status 字段通过 `repo.update()` 更新，status 变更单独通过 `repo.transition_status()` 校验。非法状态转换会显示错误通知。

**P1-1: SQL f-string 拼接安全性注释**
- 文件：`src/repository.py`
- 修复：在 `update()` 方法的 `allowed` 白名单前添加安全性说明注释。

**P1-2: 迁移层空标题容错**
- 文件：`src/migration.py`
- 修复：`_convert_task` 中对空标题 fallback 为 `"Untitled"`。

**P1-3: 迁移层缺失 in_progress 映射**
- 文件：`src/migration.py`
- 修复：`_STATUS_MAP` 添加 `"in_progress": Status.IN_PROGRESS`。

**P1-4: BacklogRepository 缺少上下文管理器**
- 文件：`src/repository.py`
- 修复：实现 `__enter__` / `__exit__` 方法，支持 `with` 语句。

**P1-5: from_dict 枚举值容错**
- 文件：`src/models.py`
- 修复：新增 `_safe_enum` 静态方法，`from_dict` 中 status 和 priority 解析使用该方法，无效值 fallback 到默认值。

#### 修改的文件
- `src/app.py`（2 处修改）
- `src/repository.py`（2 处修改）
- `src/migration.py`（2 处修改）
- `src/models.py`（3 处修改）

---

## [DEV-5-2] 修复 Select 筛选器 NoSelection bug

- **阶段：** 5
- **状态：** completed
- **时间：** 2026-03-11T00:05:00Z

### 输入
TechLeader 日志条目 TL-2-2 提供的修复方案：`on_status_filter` 和 `on_category_filter` 中 `event.value` 可能为 `Select.BLANK`（NoSelection 哨兵对象），需视为"不筛选"处理。

### 输出

#### 改动说明
在 `on_status_filter` 和 `on_category_filter` 两个方法中增加了对 `Select.BLANK` 和非字符串类型值的检查。当 `val` 为 `Select.BLANK`、非字符串类型或 `"all"` 时，均清除对应的筛选条件（设为 `None`）。

#### 修改的文件
**`/root/yanay/codes/multi-agents-demo/src/app.py`**

- **`on_status_filter`（第 327-334 行）：** 将单行三元表达式改为 if/else 结构，增加 `val == Select.BLANK or not isinstance(val, str)` 守卫条件。
- **`on_category_filter`（第 336-343 行）：** 同上，对称修改。

两处修改逻辑一致，不影响正常选择 `"all"` 或具体状态/分类值的既有行为。

---
