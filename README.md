# Backlog Manager

> 基于终端的任务管理工具 | A terminal-based task manager built with Textual TUI

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.1.0-orange)

---

## Features | 功能特性

| Feature | 功能 |
|---------|------|
| Task CRUD with category & priority | 任务增删改查，支持分类与优先级 |
| Status workflow: Todo → In Progress → Done | 状态流转：待办 → 进行中 → 完成 |
| Full-text keyword search & filter | 全文关键字搜索与过滤 |
| Trash & restore (180-day retention) | 回收站与恢复（保留 180 天） |
| JSON / CSV import & export | JSON / CSV 导入导出 |
| 7 color themes | 7 种颜色主题 |
| Column sorting (Status / Category / Priority / Age) | 列排序（状态 / 分类 / 优先级 / 天龄） |
| Priority color indicators (HIGH=red / MEDIUM=amber / LOW=green) | 优先级颜色指示（高=红 / 中=琥珀 / 低=绿） |
| Quit confirmation dialog | 退出二次确认 |
| Standard pip install | 标准 pip 安装 |
| One-command install via `install.sh` | 一键安装脚本 `install.sh` |

---

## Quick Start | 快速开始

### Option 1 — One-command install | 方式一：一键安装

```bash
git clone <repo-url>
cd backlog
bash install.sh
python -m backlog
```

### Option 2 — Manual install | 方式二：手动安装

```bash
# Requirements: Python 3.9+ | 环境要求：Python 3.9+
pip install -r requirements.txt
python -m backlog
# Alternative: python src/app.py
```

### Option 3 — pip install | 方式三：pip 安装

```bash
git clone <repo-url>
cd backlog
pip install .
backlog
# Development mode | 开发模式
pip install -e .
```

### Check version | 查看版本

```bash
python -m backlog --version
# backlog 1.1.0
```

---

## Interface Overview | 界面说明

```
┌─ Backlog Manager ─────────────────────────────────────────────────┐
│ [All Status ▼]  [All Categories ▼]                  (filter bar)  │
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

- **Filter bar | 过滤栏** — filter by Status and Category dropdowns | 按状态和分类筛选
- **Main table | 主列表** — click column headers to sort (Status / Category / Priority / Age) | 点击列标题排序
- **Status bar | 状态栏** — summary counts and pagination | 汇总数量与分页信息
- **Priority colors | 优先级颜色** — HIGH=red `#E06C75`, MEDIUM=amber `#E5C07B`, LOW=green `#98C379`

---

## Keyboard Shortcuts | 键盘快捷键

### Main View | 主界面

| Key | Action | 功能 |
|-----|--------|------|
| `↑` / `↓` | Move cursor | 移动光标 |
| `a` | Add task | 新增任务 |
| `e` | Edit task | 编辑选中任务 |
| `d` | Delete (to trash) | 删除至回收站 |
| `s` | Cycle status | 循环切换状态 |
| `t` | Open trash | 打开回收站 |
| `/` | Search / filter | 关键字搜索 |
| `n` / `p` | Next / prev page | 翻页 |
| `Ctrl+E` | Export JSON / CSV | 导出数据 |
| `Ctrl+O` | Import JSON / CSV | 导入数据 |
| `v` | Version history | 查看历史版本 |
| `Ctrl+T` | Color theme | 切换颜色主题 |
| `?` | Help | 帮助 |
| `q` | Quit (with confirmation) | 退出（需确认） |

### Add / Edit Dialog | 新增/编辑对话框

| Key | Action | 功能 |
|-----|--------|------|
| `Ctrl+S` | Save | 保存 |
| `Esc` | Cancel / Close | 取消/关闭 |

### Delete Confirmation | 删除确认

| Key | Action | 功能 |
|-----|--------|------|
| `Y` / `Enter` | Confirm delete | 确认删除 |
| `N` / `Esc` | Cancel | 取消 |

### Trash View | 回收站界面

| Key | Action | 功能 |
|-----|--------|------|
| `r` | Restore task | 恢复任务 |
| `x` | Permanently delete | 永久删除 |
| `/` | Search trash | 搜索回收站 |
| `n` / `p` | Next / prev page | 翻页 |
| `Esc` | Close trash | 关闭回收站 |

### Theme Picker | 主题选择

| Key | Action | 功能 |
|-----|--------|------|
| `↑` / `↓` | Preview theme | 预览主题（实时切换） |
| `Enter` | Apply theme | 应用选中主题 |
| `Esc` | Cancel | 取消，还原原主题 |

---

## Data Storage | 数据存储

Data is stored in `~/.backlog/backlog.db` (SQLite). Created automatically on first run.

数据存储于 `~/.backlog/backlog.db`（SQLite），首次运行自动创建，无需手动配置。

---

## Configuration | 配置

Backlog Manager stores its configuration in `~/.backlog/config.json`. You can customize the display colors for Status and Priority columns.

配置文件位于 `~/.backlog/config.json`，可自定义 Status 和 Priority 列的显示颜色。

### Example `config.json` | 示例配置

```json
{
  "status_colors": {
    "todo": "#61AFEF",
    "in_progress": "#E5C07B",
    "done": "#98C379"
  },
  "priority_colors": {
    "high": "#E06C75",
    "medium": "#E5C07B",
    "low": "#98C379"
  }
}
```

| Key | Field | Default | Description |
|-----|-------|---------|-------------|
| `status_colors` | `todo` | `#61AFEF` | Todo status color |
| | `in_progress` | `#E5C07B` | In Progress status color |
| | `done` | `#98C379` | Done status color |
| `priority_colors` | `high` | `#E06C75` | High priority color |
| | `medium` | `#E5C07B` | Medium priority color |
| | `low` | `#98C379` | Low priority color |

All color values must be valid 6-digit hex (`#RRGGBB`). Invalid or unknown keys are silently ignored, falling back to defaults.

所有颜色值须为合法的 6 位 hex（`#RRGGBB`），不合法或未知 key 将静默忽略并使用默认值。

---

## Version | 版本信息

**v1.1.0** — 2026-03-16

New in v1.1.0: Quit confirmation dialog, config.json documentation in Help screen, standard `pip install .` support via `pyproject.toml`.

v1.1.0 新增：退出二次确认对话框、Help 屏幕配置说明、pyproject.toml 标准 pip 安装支持。

**v1.0.0** — 2026-03-14

New in v1.0.0: `requirements.txt`, `python -m backlog` entry point, `--version` CLI flag, `install.sh` one-command installer.

v1.0.0 新增：依赖清单 `requirements.txt`、`python -m backlog` 入口、`--version` 标志、`install.sh` 一键安装脚本。

See [full user manual / 完整用户手册](.release/backlog-v1.1.0-用户手册.md) for details.
