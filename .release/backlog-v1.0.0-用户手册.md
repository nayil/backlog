# Backlog Manager 用户手册

**版本：v1.0.0 | 发布日期：2026-03-14**

---

## 目录

1. [简介](#简介)
2. [安装与运行](#安装与运行)
3. [界面概览](#界面概览)
4. [v1.0.0 新功能](#v100-新功能)
5. [v0.9.0 功能](#v090-功能)
6. [键盘快捷键](#键盘快捷键)
7. [功能详解](#功能详解)
8. [版本信息](#版本信息)

---

## 简介

Backlog Manager 是一款基于终端的任务管理工具（TUI），使用 [Textual](https://textual.textualize.io/) 框架构建，支持任务的创建、编辑、分类、状态流转、搜索过滤、回收站以及数据导入导出。

v1.0.0 是首个正式生产版本，在 v0.9.0 基础上补全了生产部署基础设施：依赖声明、版本常量、一键安装脚本，并将 README 升级为 GitHub 开源风格中英双语文档。

---

## 安装与运行

### 环境要求

- Python 3.9+
- 依赖库：`textual`、`rich`（见 `requirements.txt`）

### 方式一：一键安装（推荐）

```bash
git clone <repo-url>
cd backlog
bash install.sh
```

`install.sh` 会自动完成：
1. 检测 Python 3.9+（未满足则报错退出）
2. 执行 `pip install -r requirements.txt` 安装全部依赖
3. 在 `~/.local/bin/backlog` 创建启动器（可选，3 秒内按 Ctrl+C 跳过）
4. 打印安装成功提示

安装后启动：
```bash
python -m backlog
# 或（若 ~/.local/bin 已加入 PATH）
backlog
```

### 方式二：手动安装

```bash
pip install -r requirements.txt
python -m backlog
# 或：python src/app.py
```

### 查看版本

```bash
python -m backlog --version
# 输出：backlog 1.0.0
```

数据库文件默认存储于 `~/.backlog/backlog.db`，首次运行自动创建。

---

## 界面概览

```
┌─ Backlog Manager ─────────────────────────────────────────────────┐
│ [All Status ▼]  [All Categories ▼]                  (过滤栏)      │
├───────────────────────────────────────────────────────────────────┤
│ ID │ Title            │ Status ↑ │ Category │ Priority │ Age      │
│  1 │ Fix login bug    │ todo     │ backend  │ HIGH     │  3d      │
│  2 │ Write unit tests │ in_prog  │ testing  │ MEDIUM   │  1d      │
│  3 │ Update docs      │ done     │ docs     │ LOW      │  7d      │
├───────────────────────────────────────────────────────────────────┤
│ Total: 5  Todo: 3  In Progress: 1  Done: 1  Page 1/1              │
└───────────────────────────────────────────────────────────────────┘
[a]Add [e]Edit [d]Del [s]Status [t]Trash [/]Search [q]Quit
```

- **主列表**：显示任务 ID、Title、Status、Category、Priority、Age 六列
- **顶部过滤栏**：按 Status 和 Category 筛选；可搭配 `/` 关键字搜索
- **底部状态栏**：汇总数量与分页信息
- **Priority 列**：以独立颜色标识优先级（HIGH=红 / MEDIUM=琥珀 / LOW=绿）
- **列标题**：可点击排序（Status / Category / Priority / Age），活跃排序列显示 ↑/↓ 箭头

---

## v1.0.0 新功能

### F1：`requirements.txt` + `python -m backlog` 入口

**功能说明：** 新增 `requirements.txt` 声明所有依赖版本约束，并提供根目录 `__main__.py` 使项目支持 `python -m backlog` 启动方式。

**`requirements.txt` 内容：**

```
# Backlog Manager v1.0.0 dependencies
textual>=0.50.0
rich>=13.0.0
```

**安装依赖：**

```bash
pip install -r requirements.txt
```

**启动方式：**

```bash
python -m backlog        # 模块方式（推荐）
python src/app.py        # 直接运行（兼容旧方式）
```

---

### F2：`--version` CLI 参数支持

**功能说明：** `python -m backlog --version` 输出版本号后立即退出，不启动 TUI。

```bash
python -m backlog --version
# 输出：backlog 1.0.0
```

版本号定义于 `src/__init__.py`：

```python
__version__ = "1.0.0"
```

---

### F3：`install.sh` 一键部署脚本

**功能说明：** 提供全自动安装脚本，支持彩色输出（绿色=成功、黄色=提示、红色=错误），任意步骤失败立即退出。

**执行流程：**

```
[✓] Checking Python version...
[✓] Found: Python 3.x.x
[✓] Installing dependencies from requirements.txt...
[✓] Dependencies installed.
[!] Creating launcher at ~/.local/bin/backlog (optional, skip with Ctrl+C within 3s)...
[✓] Launcher created: ~/.local/bin/backlog
[✓] Backlog Manager v1.0.0 installed successfully!
```

**使用方式：**

```bash
bash install.sh
```

**注意事项：**
- 需要 Python 3.9+，检测失败时报错退出（不继续执行后续步骤）
- 启动器创建为可选步骤，3 秒内 Ctrl+C 可跳过
- 若 `~/.local/bin` 未加入 `PATH`，脚本末尾会提示添加方式

---

## v0.9.0 功能

### F1：Priority 列颜色差异化显示

**功能说明：** 主列表中，Priority 列根据优先级显示独立颜色，无需逐行阅读文字即可快速识别任务紧急程度。

**颜色对照：**

| 优先级 | 显示颜色 | 色值 |
|--------|----------|------|
| HIGH（高优先级） | 红色 | `#E06C75` |
| MEDIUM（中优先级） | 琥珀色 | `#E5C07B` |
| LOW（低优先级） | 绿色 | `#98C379` |

**使用说明：**
- 无需任何配置，颜色随 Priority 值自动显示
- 仅 Priority 列使用上述专属颜色；其余列（ID、Title、Status、Category、Age）保持原有 Category 颜色逻辑不变
- 在所有颜色主题下均有效

**适用场景：** 在大量任务中快速扫描高优先级事项，无需逐行阅读 Priority 文字。

---

### F2：列标题点击排序

**功能说明：** 点击表格列标题，可对当前视图（含过滤条件）按该列进行排序，支持升序/降序切换；活跃排序列标题右侧显示方向箭头（↑/↓）。

#### 可排序列

| 列名 | 排序逻辑 | 升序（↑）含义 | 降序（↓）含义 |
|------|----------|--------------|--------------|
| **Status** | 语义顺序 | In Progress 在前，Todo 次之，Done 最后 | Done 在前，Todo 次之，In Progress 最后 |
| **Category** | 字母顺序 | A → Z | Z → A |
| **Priority** | 语义顺序 | High 在前，Medium 次之，Low 最后 | Low 在前，Medium 次之，High 最后 |
| **Age** | 创建时间 | 最早创建的任务在前（Age 值最大） | 最近创建的任务在前（Age 值最小） |

#### 不可排序列

| 列名 | 说明 |
|------|------|
| **ID** | 点击无效，不触发排序 |
| **Title** | 点击无效，不触发排序 |

#### 交互说明

| 操作 | 效果 |
|------|------|
| 点击一个未激活的可排序列标题 | 按该列**升序（↑）**排序，列标题显示 ↑ |
| 再次点击同一列标题（当前为升序） | 切换为**降序（↓）**，列标题显示 ↓ |
| 再次点击同一列标题（当前为降序） | 切换回**升序（↑）** |
| 点击另一个可排序列标题 | 新列升序（↑）排序，旧列箭头清除 |
| 点击 ID 或 Title 列标题 | 无响应，排序状态不变 |

**分页自动重置：** 切换排序列或方向后，分页自动归位到第 1 页，确保数据显示正确，不会出现空页或数据错位。

**与过滤联动：** 排序在当前过滤结果的基础上生效。例如：先按 Status 过滤出"In Progress"任务，再点击 Priority 列标题，则仅对"In Progress"任务按 Priority 排序显示。

---

## 键盘快捷键

### 主界面

| 快捷键 | 功能 |
|--------|------|
| `↑` / `↓` | 在列表中移动光标，同时刷新右侧预览 |
| `a` | 新增任务 |
| `e` | 编辑选中任务 |
| `d` | 删除选中任务（移入回收站） |
| `s` | 循环切换状态：Todo → In Progress → Done → In Progress |
| `t` | 打开回收站 |
| `/` | 打开关键字搜索/过滤 |
| `n` | 下一页 |
| `p` | 上一页 |
| `Ctrl+E` | 导出数据（JSON / CSV） |
| `Ctrl+O` | 导入数据（JSON / CSV） |
| `v` | 查看历史版本列表 |
| `Ctrl+T` | 切换颜色主题 |
| `?` | 显示帮助（快捷键说明） |
| `q` | 退出应用 |

### 新增/编辑对话框

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+S` | 保存 |
| `Esc` | 取消，关闭对话框 |

### 删除确认对话框

| 快捷键 | 功能 |
|--------|------|
| `Y` 或 `Enter` | 确认删除 |
| `N` 或 `Esc` | 取消 |

### 回收站界面

| 快捷键 | 功能 |
|--------|------|
| `r` | 恢复选中任务 |
| `x` | 永久删除选中任务 |
| `/` | 搜索回收站 |
| `n` | 下一页 |
| `p` | 上一页 |
| `Esc` | 关闭回收站 |

### 主题选择界面

| 快捷键 | 功能 |
|--------|------|
| `↑` / `↓` | 预览主题（实时切换） |
| `Enter` | 应用选中主题 |
| `Esc` | 取消，还原原主题 |

### 帮助/版本界面

| 快捷键 | 功能 |
|--------|------|
| `Esc` 或 `q` | 关闭界面 |

---

## 功能详解

### 任务字段说明

| 字段 | 说明 |
|------|------|
| **Title** | 必填；建议格式 `category:描述`，系统自动识别冒号前缀为 Category |
| **Description** | 选填，自由文本备注；支持右侧面板快速预览 |
| **Category** | 选填；输入时自动提示已有 Category；影响列表颜色（Category 颜色逻辑） |
| **Priority** | High / Medium（默认）/ Low；Priority 列以专属颜色显示 |
| **Status** | 新建时固定为 Todo；编辑时可手动设置任意值 |

### 状态流转

```
Todo  --[s]-->  In Progress  --[s]-->  Done  --[s]-->  In Progress
```

使用 `s` 键一键循环切换，或在编辑对话框中手动指定任意状态。

### 回收站

- 删除的任务进入回收站，**保留 180 天**后自动过期
- 回收站内可搜索、恢复或永久删除
- 永久删除需二次确认

### 数据导入导出

- 支持 **JSON** 和 **CSV** 两种格式
- 导出：`Ctrl+E`，选择格式和路径后保存
- 导入：`Ctrl+O`，选择文件后导入；空标题或已删除记录自动跳过

### 颜色主题

按 `Ctrl+T` 打开主题选择器，支持以下 7 种主题：

| 主题名称 | 描述 |
|----------|------|
| textual-dark | 默认暗色 |
| backlog-light | 清爽亮色 |
| backlog-nord | 北欧冷蓝 |
| backlog-solarized-light | Solarized 护眼暖白 |
| backlog-solarized-dark | Solarized 护眼暗色 |
| backlog-gruvbox | 复古终端暖黄绿 |
| backlog-dracula | 流行紫色暗色 |

主题选择实时预览，`Enter` 确认后持久化保存。

---

## 版本信息

### v1.0.0（当前版本）

| 项目 | 内容 |
|------|------|
| **版本号** | v1.0.0 |
| **发布日期** | 2026-03-14 |
| **技术框架** | Python 3.9+ + Textual TUI |
| **数据存储** | SQLite（`~/.backlog/backlog.db`） |

#### v1.0.0 新增功能

| 编号 | 功能 | 说明 |
|------|------|------|
| F1 | `requirements.txt` + `python -m backlog` | 依赖声明与模块入口 |
| F2 | `--version` CLI 参数 | 输出 `backlog 1.0.0` 后退出，不启动 TUI |
| F3 | `install.sh` 一键部署 | Python 检测、pip 安装、启动器创建、彩色输出 |

#### v1.0.0 新增/修改文件

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `requirements.txt` | 新建 | textual>=0.50.0, rich>=13.0.0 |
| `__main__.py` | 新建 | `python -m backlog` 入口，含 `--version` 检测 |
| `src/__init__.py` | 新建 | `__version__ = "1.0.0"` 包元数据 |
| `install.sh` | 新建 | 一键安装脚本（Bash） |
| `README.md` | 全量重写 | GitHub 开源风格中英双语 |

---

### 历史版本对比

| 对比维度 | v0.8.0 | v0.9.0 | v1.0.0 |
|----------|--------|--------|--------|
| Priority 列颜色 | 跟随 Category 颜色 | 独立颜色：HIGH=红、MEDIUM=琥珀、LOW=绿 | 同 v0.9.0 |
| 列排序 | 固定按 ID 升序 | 点击 Status/Category/Priority/Age 列头可切换升降序 | 同 v0.9.0 |
| 依赖声明 | 无 `requirements.txt` | 无 `requirements.txt` | 新增 `requirements.txt` |
| 启动方式 | `python src/app.py` | `python src/app.py` | `python -m backlog`（新增），`python src/app.py`（保留） |
| 版本查询 | 不支持 | 不支持 | `python -m backlog --version` |
| 一键安装 | 不支持 | 不支持 | `bash install.sh` |
| 测试覆盖 | 基础测试 | 17 个新增测试（排序、颜色、联动） | 全部通过（无新增测试） |

---

*本用户手册适用于 Backlog Manager v1.0.0，发布日期 2026-03-14。*
