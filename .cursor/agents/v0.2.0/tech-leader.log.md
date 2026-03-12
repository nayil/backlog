## [TL-2-1] 技术调研与方案设计：三项功能改进

- **阶段：** 2
- **状态：** completed
- **时间：** 2026-03-12T00:00:00

### 输入

需求描述：
1. 修复 log 状态变更（Edit 表单保存后不生效）的问题
2. 展示每条 log 自创建日期至当前时间经过了多少天
3. 在 UI 中展示可用的历史版本列表，版本信息从 `release/` 目录下的文件名推断

目标文件：`src/app.py`、`src/models.py`、`src/repository.py`、`src/migration.py`
Worktree 路径：`.worktrees/v0.2.0/`

---

### 输出

---

## 一、技术调研结论

### 1. Bug 分析：状态变更保存后不生效

**根因定位（`src/app.py` `action_edit_item`，第 671-703 行）：**

```python
def on_result(result: Optional[BacklogItem]) -> None:
    if result is not None:
        # Update non-status fields directly
        self.repo.update(
            item_id,
            title=result.title,
            description=result.description,
            category=result.category,
            priority=result.priority,
        )
        # Use transition_status for status changes to enforce validation
        if result.status != item.status:
            try:
                self.repo.transition_status(item_id, result.status)
            ...
```

**问题所在：** `item` 变量是在 `action_edit_item` 外层捕获的闭包引用，指向从 `repo.get(item_id)` 获取的原始对象。`ItemFormScreen` 的 `action_submit`（第 154-162 行）直接修改了 `self.item` 对象的字段（包括 `self.item.status`），然后 `dismiss(self.item)` 返回的是**同一个对象引用**。

因此，当回调函数中执行 `result.status != item.status` 比较时，`result` 和 `item` 是**同一个对象**，比较永远为 `False`，`transition_status` 永远不会被调用，状态变更被静默丢弃。

**修复思路：** 在 `action_edit_item` 的回调中，在推送 `ItemFormScreen` 之前，记录 `item.status` 的快照值（如 `original_status = item.status`），与 `result.status` 比较。

---

### 2. 功能分析：展示经过天数（Age）

**现状：**
- `BacklogItem` 已有 `created_at: Optional[datetime]` 字段（`models.py` 第 32 行）
- `repository.py` 的 `_row_to_item` 正确解析 `created_at`
- `app.py` 的 `_refresh_table` 列定义为 `"ID", "Title", "Status", "Category", "Priority"`，未包含日期/天数列（第 575 行）

**实现思路：** 在 `_refresh_table` 的列和行渲染中新增 `"Age"` 列，值为 `(datetime.now() - item.created_at).days`，显示为 `{n}d` 格式。无需修改 model 或 repository。

---

### 3. 功能分析：历史版本列表

**现状：**
- `release/` 目录下已有文件：
  - `backlog-manager-v0.1.0-用户手册.md`
  - `backlog-manager-v0.2.0-user-manual.md`
  - `backlog-manager-v0.2.0-用户手册.md`
- 版本号可通过正则从文件名提取：`v\d+\.\d+\.\d+`

**实现思路：**
- 新增 `VersionScreen`（`ModalScreen`）：扫描 `release/` 目录，提取去重、排序后的版本号列表，以 `DataTable` 展示
- 在 `BacklogApp` 中新增快捷键 `v`（`action_show_versions`）
- `release/` 目录路径需动态计算（相对于 `app.py` 所在目录的上层目录，或从 `DB_PATH` 推断项目根目录）
- 若 `release/` 目录不存在或为空，给出友好提示

---

## 二、模块划分

| 模块 | 职责 | 修改文件 | 接口变更 |
|------|------|----------|---------|
| **A. Bug Fix: Status** | 修复 `action_edit_item` 中状态比较的闭包陷阱 | `src/app.py` | 无新接口，仅内部逻辑修复 |
| **B. Age Column** | 在主列表新增 "Age" 展示列 | `src/app.py` | 无新接口，在 `_refresh_table` 中计算并渲染 |
| **C. Version Screen** | 新增版本历史 Modal 屏幕 | `src/app.py` | 新增 `VersionScreen` 类；`BacklogApp` 新增 `action_show_versions` 方法和 `v` 快捷键 |

**三个模块完全独立，无互相依赖，可并行开发。**

---

## 三、接口定义

### 模块 A：状态 Bug 修复

**修改位置：** `BacklogApp.action_edit_item`（`src/app.py` 第 671 行）

```python
# 修复前（伪代码）：
item = self.repo.get(item_id)
def on_result(result):
    if result.status != item.status:  # item 被 ItemFormScreen 修改，比较失效
        self.repo.transition_status(...)

# 修复后（伪代码）：
item = self.repo.get(item_id)
original_status = item.status  # 在 push_screen 前记录快照
def on_result(result):
    if result.status != original_status:  # 与快照比较，正确
        self.repo.transition_status(...)
```

**约束：** `transition_status` 的合法转换规则（`TODO→IN_PROGRESS`、`IN_PROGRESS→DONE/TODO`、`DONE→IN_PROGRESS`）保持不变，不放宽校验。

---

### 模块 B：Age 列

**修改位置：** `BacklogApp.on_mount` 和 `BacklogApp._refresh_table`（`src/app.py`）

- `on_mount`：列定义改为 `"ID", "Title", "Status", "Category", "Priority", "Age"`
- `_refresh_table`：每行新增 age 值：

```python
from datetime import datetime

age = (datetime.now() - item.created_at).days if item.created_at else "-"
age_str = f"{age}d" if isinstance(age, int) else age

table.add_row(
    str(item.id), item.title,
    STATUS_DISPLAY.get(item.status, item.status.value),
    item.category or "-",
    PRIORITY_DISPLAY.get(item.priority, item.priority.value),
    age_str,
    key=str(item.id),
)
```

**约束：** `datetime` 已在 `app.py` 中通过 models 间接可用，需确认直接 import。

---

### 模块 C：VersionScreen

**新增类：** `VersionScreen(ModalScreen[None])`

```python
class VersionScreen(ModalScreen[None]):
    """Modal screen displaying available historical versions from release/ directory."""
    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]

    def _get_release_dir(self) -> Path:
        # release/ 相对于 app.py 所在目录的上层
        return Path(__file__).resolve().parent.parent / "release"

    def _parse_versions(self) -> list[str]:
        import re
        release_dir = self._get_release_dir()
        if not release_dir.exists():
            return []
        versions = set()
        for f in release_dir.iterdir():
            match = re.search(r'v(\d+\.\d+\.\d+)', f.name)
            if match:
                versions.add(match.group(0))
        # 按语义版本排序（major.minor.patch 降序）
        return sorted(versions, key=lambda v: tuple(int(x) for x in v[1:].split('.')), reverse=True)

    def compose(self) -> ComposeResult:
        # DataTable 展示版本号列表，含文件名详情
        ...
```

**BacklogApp 变更：**
- 新增 `Binding("v", "show_versions", "Versions")` 到 `BINDINGS`
- 新增 `action_show_versions` 方法

---

## 四、开发计划

| 顺序 | 模块 | 说明 |
|------|------|------|
| 并行（同批次） | A、B、C | 三者无依赖，可同时交给一个 Developer 或分拆为多个 |

由于三个改动都集中在 `src/app.py`，**建议由单一 Developer 顺序实现**，避免合并冲突。实现顺序建议：A（Bug Fix，最小改动、优先修复）→ B（Age 列）→ C（VersionScreen）。

---

## 五、技术风险与应对

| 风险 | 等级 | 应对措施 |
|------|------|---------|
| `release/` 目录路径在不同运行目录下解析不一致 | P1 | 使用 `Path(__file__).resolve().parent.parent / "release"` 基于脚本位置定位，而非 CWD |
| 版本排序依赖字符串解析，若文件名格式不规范会导致漏读 | P2 | 正则仅提取 `v\d+\.\d+\.\d+` 格式，不匹配的文件名静默跳过，有无结果都展示提示信息 |
| `item.created_at` 为 None 时 Age 计算崩溃 | P1 | 加 `if item.created_at` 守卫，显示 `-` |
| 状态修复后 `transition_status` 校验阻止合法的编辑场景（如从 Done 直接改为 Todo） | P1 | 当前 `transition_status` 不支持 `DONE→TODO`；Edit 表单应尊重这个约束，失败时展示错误通知（已有 `except ValueError` 处理，行为保持一致） |
| `datetime` 未在 `app.py` 顶层 import | P2 | 检查并在文件头部补充 `from datetime import datetime` |

---

### 输出文件

- `.cursor/agents/v0.2.0/tech-leader.log.md`（本文件）

---
