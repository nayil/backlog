# Column Color Independent Control Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the theme system and implement user-configurable per-enum-value colors for Status and Priority columns via `~/.backlog/config.json`.

**Architecture:** New `ColorConfig` class manages color settings, delegating file I/O to `BacklogConfig`. The colorize functions in `colors.py` accept a `ColorConfig` parameter instead of using hardcoded constants. Theme system is fully removed.

**Tech Stack:** Python, Textual, Rich (Text), JSON config, pytest/unittest

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `src/color_config.py` | Create | Color configuration: defaults, load/save, validation |
| `src/colors.py` | Modify | Colorize functions accept `ColorConfig`; remove color constants and category functions |
| `src/config.py` | Modify | Remove theme methods; keep `_load`/`_save` infrastructure |
| `src/app.py` | Modify | Remove theme code; wire `ColorConfig` into table rendering |
| `src/screens/__init__.py` | Modify | Remove `ThemeScreen` export |
| `src/screens/help_screen.py` | Modify | Remove Ctrl+T line |
| `src/themes.py` | Delete | No longer needed |
| `src/screens/theme_screen.py` | Delete | No longer needed |
| `tests/test_v090.py` | Rewrite | Update for new color system, remove theme/category tests |
| `tests/test_app_v080.py` | Modify | Remove `CATEGORY_COLORS`/`category_color` imports and tests |
| `tests/test_color_config.py` | Create | Unit tests for `ColorConfig` |

---

## Chunk 1: ColorConfig with TDD

### Task 1: Create `ColorConfig` class with tests

**Files:**
- Create: `tests/test_color_config.py`
- Create: `src/color_config.py`

- [ ] **Step 1: Write failing tests for ColorConfig**

Create `tests/test_color_config.py`:

```python
"""Tests for ColorConfig: user-configurable Status/Priority colors."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from color_config import ColorConfig


class TestColorConfigDefaults(unittest.TestCase):
    """When no config file exists, all defaults are returned."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_default_status_colors(self):
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")
        self.assertEqual(cc.get_status_color("in_progress"), "#E5C07B")
        self.assertEqual(cc.get_status_color("done"), "#98C379")

    def test_default_priority_colors(self):
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_priority_color("high"), "#E06C75")
        self.assertEqual(cc.get_priority_color("medium"), "#E5C07B")
        self.assertEqual(cc.get_priority_color("low"), "#98C379")


class TestColorConfigUserOverrides(unittest.TestCase):
    """User overrides in config.json take precedence over defaults."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_partial_status_override(self):
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"todo": "#FF0000"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#FF0000")
        # Non-overridden values still use defaults
        self.assertEqual(cc.get_status_color("done"), "#98C379")

    def test_partial_priority_override(self):
        with open(self.config_file, "w") as f:
            json.dump({"priority_colors": {"high": "#00FF00"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_priority_color("high"), "#00FF00")
        self.assertEqual(cc.get_priority_color("low"), "#98C379")


class TestColorConfigUnknownKeys(unittest.TestCase):
    """Unknown keys in config are silently ignored."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_unknown_status_key_ignored(self):
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"nonexistent": "#FF0000"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        # Unknown key returns empty string (no default exists)
        self.assertEqual(cc.get_status_color("nonexistent"), "")
        # Known keys still return defaults
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")


class TestColorConfigInvalidHex(unittest.TestCase):
    """Invalid hex values in config fall back to defaults."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_invalid_hex_falls_back(self):
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"todo": "not-a-color"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")

    def test_non_string_value_falls_back(self):
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"todo": 12345}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")


class TestColorConfigMalformedJson(unittest.TestCase):
    """Malformed config.json falls back to all defaults."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_malformed_json(self):
        with open(self.config_file, "w") as f:
            f.write("{invalid json")
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")


class TestColorConfigSetters(unittest.TestCase):
    """Setters validate and persist colors."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_set_status_color_persists(self):
        cc = ColorConfig(config_path=self.config_file)
        cc.set_status_color("todo", "#FF0000")
        # Re-load from disk
        cc2 = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc2.get_status_color("todo"), "#FF0000")

    def test_set_priority_color_persists(self):
        cc = ColorConfig(config_path=self.config_file)
        cc.set_priority_color("high", "#00FF00")
        cc2 = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc2.get_priority_color("high"), "#00FF00")

    def test_set_invalid_hex_raises(self):
        cc = ColorConfig(config_path=self.config_file)
        with self.assertRaises(ValueError):
            cc.set_status_color("todo", "not-valid")

    def test_set_preserves_other_config_keys(self):
        # Existing config with a "theme" key should not be destroyed
        with open(self.config_file, "w") as f:
            json.dump({"theme": "old-theme", "other": 42}, f)
        cc = ColorConfig(config_path=self.config_file)
        cc.set_status_color("todo", "#AABBCC")
        with open(self.config_file) as f:
            data = json.load(f)
        self.assertEqual(data["other"], 42)
        self.assertEqual(data["theme"], "old-theme")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /root/yanay/codes/backlog/.worktrees/v0.9.0 && python -m pytest tests/test_color_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'color_config'`

- [ ] **Step 3: Implement ColorConfig**

Create `src/color_config.py`:

```python
"""User-configurable color settings for Status and Priority columns."""

from __future__ import annotations

import re

from config import BacklogConfig

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ColorConfig:
    """Manages per-enum-value text colors for Status and Priority.

    Delegates file I/O to ``BacklogConfig`` (composition) to avoid
    two classes independently writing to the same JSON file.
    """

    DEFAULT_STATUS_COLORS: dict[str, str] = {
        "todo": "#61AFEF",
        "in_progress": "#E5C07B",
        "done": "#98C379",
    }

    DEFAULT_PRIORITY_COLORS: dict[str, str] = {
        "high": "#E06C75",
        "medium": "#E5C07B",
        "low": "#98C379",
    }

    def __init__(self, config_path: str | None = None) -> None:
        self._bc = BacklogConfig(config_path) if config_path else BacklogConfig()
        self._status: dict[str, str] = {}
        self._priority: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        data = self._bc._load()
        self._status = self._validated(data.get("status_colors", {}))
        self._priority = self._validated(data.get("priority_colors", {}))

    @staticmethod
    def _validated(mapping: object) -> dict[str, str]:
        if not isinstance(mapping, dict):
            return {}
        return {k: v for k, v in mapping.items()
                if isinstance(v, str) and _HEX_RE.match(v)}

    def get_status_color(self, status_value: str) -> str:
        return self._status.get(
            status_value,
            self.DEFAULT_STATUS_COLORS.get(status_value, ""),
        )

    def get_priority_color(self, priority_value: str) -> str:
        return self._priority.get(
            priority_value,
            self.DEFAULT_PRIORITY_COLORS.get(priority_value, ""),
        )

    def set_status_color(self, status_value: str, color: str) -> None:
        if not _HEX_RE.match(color):
            raise ValueError(f"Invalid hex color: {color!r}")
        data = self._bc._load()
        colors = data.setdefault("status_colors", {})
        colors[status_value] = color
        self._bc._save(data)
        self._status[status_value] = color

    def set_priority_color(self, priority_value: str, color: str) -> None:
        if not _HEX_RE.match(color):
            raise ValueError(f"Invalid hex color: {color!r}")
        data = self._bc._load()
        colors = data.setdefault("priority_colors", {})
        colors[priority_value] = color
        self._bc._save(data)
        self._priority[priority_value] = color
```

**Note:** `BacklogConfig.__init__` needs to accept an optional `config_path` parameter for testability. Update `config.py` in Task 1 Step 3 as well — add `config_path` parameter to `BacklogConfig.__init__`:

```python
class BacklogConfig:
    def __init__(self, config_path: str | None = None) -> None:
        if config_path:
            self._config_file = Path(config_path)
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            self._config_file = CONFIG_FILE

    def _load(self) -> dict:
        try:
            with self._config_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict) -> None:
        try:
            with self._config_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            import sys
            print(f"[backlog] warning: failed to save config: {exc}", file=sys.stderr)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /root/yanay/codes/backlog/.worktrees/v0.9.0 && python -m pytest tests/test_color_config.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/color_config.py tests/test_color_config.py
git commit -m "feat: add ColorConfig for user-configurable Status/Priority colors"
```

---

## Chunk 2: Update colors.py and its tests

### Task 2: Modify `colors.py` to use `ColorConfig`

**Files:**
- Modify: `src/colors.py`
- Modify: `tests/test_v090.py`

- [ ] **Step 1: Update tests for new colorize signatures**

Replace `tests/test_v090.py` with:

```python
"""Tests for v0.9.0: colors module and screens imports."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rich.text import Text

from models import Status, Priority
from colors import (
    STATUS_DISPLAY,
    PRIORITY_DISPLAY,
    NEXT_STATUS,
    colorize_status,
    colorize_priority,
)
from color_config import ColorConfig


# ── colors.py tests ─────────────────────────────────────────────────────────


class TestStatusDisplayMapping(unittest.TestCase):
    def test_status_display_mapping(self):
        for s in Status:
            self.assertIn(s, STATUS_DISPLAY, f"{s} missing from STATUS_DISPLAY")


class TestPriorityDisplayMapping(unittest.TestCase):
    def test_priority_display_mapping(self):
        for p in Priority:
            self.assertIn(p, PRIORITY_DISPLAY, f"{p} missing from PRIORITY_DISPLAY")


class TestNextStatusMapping(unittest.TestCase):
    def test_next_status_mapping(self):
        self.assertEqual(NEXT_STATUS[Status.TODO], Status.IN_PROGRESS)
        self.assertEqual(NEXT_STATUS[Status.IN_PROGRESS], Status.DONE)
        self.assertEqual(NEXT_STATUS[Status.DONE], Status.IN_PROGRESS)


class TestColorizeStatusWithConfig(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.cc = ColorConfig(config_path=self.config_file)

    def test_returns_text(self):
        result = colorize_status(Status.TODO, self.cc)
        self.assertIsInstance(result, Text)

    def test_uses_default_color(self):
        result = colorize_status(Status.TODO, self.cc)
        style_str = str(result.style) if result.style else ""
        self.assertIn("#61afef", style_str.lower())

    def test_uses_custom_color(self):
        import json
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"todo": "#FF0000"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        result = colorize_status(Status.TODO, cc)
        style_str = str(result.style) if result.style else ""
        self.assertIn("#ff0000", style_str.lower())


class TestColorizePriorityWithConfig(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")
        self.cc = ColorConfig(config_path=self.config_file)

    def test_returns_text(self):
        result = colorize_priority(Priority.HIGH, self.cc)
        self.assertIsInstance(result, Text)

    def test_uses_default_color(self):
        result = colorize_priority(Priority.HIGH, self.cc)
        style_str = str(result.style) if result.style else ""
        self.assertIn("#e06c75", style_str.lower())


# ── screens/ import tests ───────────────────────────────────────────────────


class TestScreensImport(unittest.TestCase):
    def test_import_all_screens(self):
        from screens import (
            ItemFormScreen,
            SearchScreen,
            ConfirmDeleteScreen,
            TrashScreen,
            HelpScreen,
            VersionScreen,
            ExportScreen,
            ImportScreen,
        )
        classes = [
            ItemFormScreen, SearchScreen, ConfirmDeleteScreen,
            TrashScreen, HelpScreen, VersionScreen,
            ExportScreen, ImportScreen,
        ]
        self.assertEqual(len(classes), 8)

    def test_screen_classes_are_modal(self):
        from textual.screen import ModalScreen
        from screens import (
            ItemFormScreen, SearchScreen, ConfirmDeleteScreen,
            TrashScreen, HelpScreen, VersionScreen,
            ExportScreen, ImportScreen,
        )
        for cls in [
            ItemFormScreen, SearchScreen, ConfirmDeleteScreen,
            TrashScreen, HelpScreen, VersionScreen,
            ExportScreen, ImportScreen,
        ]:
            self.assertTrue(
                issubclass(cls, ModalScreen),
                f"{cls.__name__} is not a subclass of ModalScreen",
            )


# ── app.py line count test ──────────────────────────────────────────────────


class TestAppLineCount(unittest.TestCase):
    def test_app_line_count(self):
        app_path = os.path.join(os.path.dirname(__file__), "..", "src", "app.py")
        with open(app_path) as f:
            line_count = sum(1 for _ in f)
        self.assertLessEqual(line_count, 500, f"app.py has {line_count} lines, exceeds 500")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /root/yanay/codes/backlog/.worktrees/v0.9.0 && python -m pytest tests/test_v090.py -v`
Expected: FAIL — `colorize_status() takes 1 positional argument but 2 were given`

- [ ] **Step 3: Update `colors.py`**

Replace `src/colors.py` with:

```python
"""Centralized colorization functions for Status and Priority columns."""

from __future__ import annotations

from rich.text import Text

from models import Priority, Status

# ── Display text mappings ────────────────────────────────────────────

STATUS_DISPLAY: dict[Status, str] = {
    Status.TODO: "Todo",
    Status.IN_PROGRESS: "In Progress",
    Status.DONE: "Done",
}

PRIORITY_DISPLAY: dict[Priority, str] = {
    Priority.HIGH: "High",
    Priority.MEDIUM: "Medium",
    Priority.LOW: "Low",
}

# ── Status cycle mapping ─────────────────────────────────────────────

NEXT_STATUS: dict[Status, Status] = {
    Status.TODO: Status.IN_PROGRESS,
    Status.IN_PROGRESS: Status.DONE,
    Status.DONE: Status.IN_PROGRESS,
}

# ── Color functions ──────────────────────────────────────────────────


def colorize_status(status: Status, color_config) -> Text:
    """Return a Rich Text with the status display name colored per config."""
    display = STATUS_DISPLAY.get(status, str(status.value))
    color = color_config.get_status_color(status.value)
    return Text(display, style=color) if color else Text(display)


def colorize_priority(priority: Priority, color_config) -> Text:
    """Return a Rich Text with the priority display name colored per config."""
    display = PRIORITY_DISPLAY.get(priority, str(priority.value))
    color = color_config.get_priority_color(priority.value)
    return Text(display, style=color) if color else Text(display)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /root/yanay/codes/backlog/.worktrees/v0.9.0 && python -m pytest tests/test_v090.py tests/test_color_config.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/colors.py tests/test_v090.py
git commit -m "refactor: colors.py uses ColorConfig, remove color constants and category functions"
```

---

## Chunk 3: Remove theme system and update app.py

### Task 3: Remove theme system

**Files:**
- Delete: `src/themes.py`
- Delete: `src/screens/theme_screen.py`
- Modify: `src/screens/__init__.py`
- Modify: `src/screens/help_screen.py`
- Modify: `src/config.py`
- Modify: `src/app.py`

- [ ] **Step 1: Remove `ThemeScreen` from `screens/__init__.py`**

Remove line 9: `from screens.theme_screen import ThemeScreen`

New contents:
```python
from screens.item_form import ItemFormScreen
from screens.search import SearchScreen
from screens.confirm_delete import ConfirmDeleteScreen
from screens.trash import TrashScreen
from screens.help_screen import HelpScreen
from screens.version import VersionScreen
from screens.export import ExportScreen
from screens.import_screen import ImportScreen
```

- [ ] **Step 2: Delete theme files**

```bash
git rm src/themes.py src/screens/theme_screen.py
```

- [ ] **Step 3: Remove Ctrl+T from `help_screen.py`**

Delete line 70: `yield Label("   Ctrl+T         Switch color theme")`

- [ ] **Step 4: Clean up `config.py`**

Remove `DEFAULT_THEME` constant (line 10), `get_theme`/`set_theme` methods (lines 34-43), and module-level `get_theme`/`set_theme` functions (lines 54-59). Keep `load_config`/`save_config`.

New contents:
```python
"""Persistent configuration for Backlog Manager."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR: Path = Path.home() / ".backlog"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"


class BacklogConfig:
    """Manages persistent configuration stored in ~/.backlog/config.json."""

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict) -> None:
        try:
            with CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            import sys
            print(f"[backlog] warning: failed to save config: {exc}", file=sys.stderr)


def load_config() -> dict:
    return BacklogConfig()._load()


def save_config(config: dict) -> None:
    BacklogConfig()._save(config)
```

- [ ] **Step 5: Update `app.py`**

Changes:
1. Remove imports: `colorize_category` from colors, `CUSTOM_THEMES`/`AVAILABLE_THEMES` from themes, `ThemeScreen` from screens
2. Add import: `from color_config import ColorConfig`
3. Remove `Binding("ctrl+t", "change_theme", "Theme")` from BINDINGS
4. In `__init__`: add `self.color_config = ColorConfig()`
5. In `on_mount`: remove theme registration loop (lines 162-163) and theme loading (lines 177-179)
6. In `_refresh_table`: change `colorize_status(item.status)` to `colorize_status(item.status, self.color_config)`, change `colorize_priority(item.priority)` to `colorize_priority(item.priority, self.color_config)`, change `colorize_category(item.category or "-")` to `item.category or "-"`
7. Remove `action_change_theme` method (lines 450-457)

Updated `app.py`:

```python
"""Backlog Manager TUI application using Textual."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Select,
    Static,
)

# Ensure src/ is on the path so models/repository can be imported directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from colors import (
    STATUS_DISPLAY,
    PRIORITY_DISPLAY,
    NEXT_STATUS,
    colorize_status,
    colorize_priority,
)
from color_config import ColorConfig
from screens import (
    ItemFormScreen,
    SearchScreen,
    ConfirmDeleteScreen,
    TrashScreen,
    HelpScreen,
    VersionScreen,
    ExportScreen,
    ImportScreen,
)
from config import BacklogConfig
from models import BacklogItem, Priority, Status
from repository import BacklogRepository

DB_PATH = os.path.join(Path.home(), ".backlog", "backlog.db")

# ── sort column mapping ───────────────────────────────────────────────

_COL_TO_SORT = {
    "Status": "status",
    "Category": "category",
    "Priority": "priority",
    "Age": "age",
}

# ── Main App ────────────────────────────────────────────────────────


class BacklogApp(App):
    """TUI Backlog Manager."""

    TITLE = "Backlog Manager"
    CSS = """
    #filter-bar {
        height: 3;
        dock: top;
        padding: 0 1;
    }
    #filter-bar Select {
        width: 24;
        margin-right: 1;
    }
    #stats-bar {
        height: 1;
        dock: bottom;
        padding: 0 1;
        background: $accent;
        color: $text;
    }
    #main-content {
        height: 1fr;
    }
    #table {
        width: 65%;
        height: 100%;
    }
    #preview-panel {
        width: 35%;
        border-left: solid $primary;
        padding: 0 1;
    }
    #preview-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    #preview-desc {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("a", "add_item", "Add"),
        Binding("e", "edit_item", "Edit"),
        Binding("d", "delete_item", "Delete"),
        Binding("s", "toggle_status", "Status"),
        Binding("t", "open_trash", "Trash"),
        Binding("ctrl+e", "export_data", "Export"),
        Binding("ctrl+o", "import_data", "Import"),
        Binding("v", "show_versions", "Versions"),
        Binding("slash", "search", "Search"),
        Binding("n", "next_page", "Next Page"),
        Binding("p", "prev_page", "Prev Page"),
        Binding("question_mark", "help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, db_path: str = DB_PATH) -> None:
        super().__init__()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.repo = BacklogRepository(db_path)
        self.config = BacklogConfig()
        self.color_config = ColorConfig()
        self.filter_status: Optional[Status] = None
        self.filter_category: Optional[str] = None
        self.filter_keyword: Optional[str] = None
        self.page: int = 0
        self.page_size: int = 20
        self._total_count: int = 0
        self._sort_by: Optional[str] = None
        self._sort_asc: bool = True
        self._col_keys: dict = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="filter-bar"):
            yield Select(
                [("All Status", "all")]
                + [(s.value.replace("_", " ").capitalize(), s.value) for s in Status],
                value="all",
                id="sel-filter-status",
            )
            yield Select(
                [("All Categories", "all")],
                value="all",
                id="sel-filter-category",
            )
        with Horizontal(id="main-content"):
            yield DataTable(id="table")
            with VerticalScroll(id="preview-panel"):
                yield Static("", id="preview-title")
                yield Static("", id="preview-desc")
        yield Static("", id="stats-bar")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.cursor_type = "row"
        col_keys = table.add_columns("ID", "Title", "Status", "Category", "Priority", "Age")
        self._col_keys = {
            "ID": col_keys[0],
            "Title": col_keys[1],
            "Status": col_keys[2],
            "Category": col_keys[3],
            "Priority": col_keys[4],
            "Age": col_keys[5],
        }
        self._refresh_categories()
        self._refresh_table()

    # ── data refresh ─────────────────────────────────────────────

    def _refresh_table(self) -> None:
        table = self.query_one("#table", DataTable)
        table.clear()
        table.move_cursor(row=0, animate=False)
        items = self.repo.list(
            status=self.filter_status,
            category=self.filter_category,
            keyword=self.filter_keyword,
            limit=self.page_size,
            offset=self.page * self.page_size,
            sort_by=self._sort_by,
            sort_asc=self._sort_asc,
        )
        now = datetime.now()
        for item in items:
            age_str = f"{(now - item.created_at).days}d" if item.created_at else "-"
            table.add_row(
                str(item.id),
                item.title,
                colorize_status(item.status, self.color_config),
                item.category or "-",
                colorize_priority(item.priority, self.color_config),
                age_str,
                key=str(item.id),
            )
        table.refresh()
        if not items:
            self._clear_preview()
        self._refresh_stats()

    def _refresh_stats(self) -> None:
        stats = self.repo.get_stats(category=self.filter_category)
        by_s = stats["by_status"]
        self._total_count = self.repo.count(
            status=self.filter_status,
            category=self.filter_category,
            keyword=self.filter_keyword,
        )
        total_pages = max(1, (self._total_count + self.page_size - 1) // self.page_size)
        current_page = self.page + 1
        bar = self.query_one("#stats-bar", Static)
        bar.update(
            f" Total: {self._total_count}  |  "
            f"Todo: {by_s.get('todo', 0)}  |  "
            f"In Progress: {by_s.get('in_progress', 0)}  |  "
            f"Done: {by_s.get('done', 0)}  |  "
            f"Page {current_page}/{total_pages}  [N]ext  [P]rev"
        )

    def _refresh_categories(self) -> None:
        sel = self.query_one("#sel-filter-category", Select)
        categories = self.repo.get_categories()
        options = [("All Categories", "all")] + [(c, c) for c in categories]
        sel.set_options(options)

    def _selected_item_id(self) -> Optional[int]:
        table = self.query_one("#table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            return int(row_key.value)
        except Exception:
            return None

    def _clear_preview(self) -> None:
        self.query_one("#preview-title", Static).update("")
        self.query_one("#preview-desc", Static).update("")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None:
            return
        try:
            item_id = int(str(event.row_key.value))
        except (ValueError, TypeError):
            return
        item = self.repo.get(item_id)
        if item:
            self.query_one("#preview-title", Static).update(item.title or "")
            self.query_one("#preview-desc", Static).update(item.description or "(No description)")
        else:
            self._clear_preview()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        col_label = str(event.label).rstrip(" \u2191\u2193").strip()
        sort_field = _COL_TO_SORT.get(col_label)
        if sort_field is None:
            return
        if self._sort_by == sort_field:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_by = sort_field
            self._sort_asc = True
        self.page = 0
        self._update_column_labels()
        self._refresh_table()

    def _update_column_labels(self) -> None:
        table = self.query_one("#table", DataTable)
        base_labels = {
            "ID": "ID", "Title": "Title", "Status": "Status",
            "Category": "Category", "Priority": "Priority", "Age": "Age"
        }
        sort_col = {v: k for k, v in _COL_TO_SORT.items()}.get(self._sort_by)
        for col_name, col_key in self._col_keys.items():
            label = base_labels[col_name]
            if col_name == sort_col:
                label += " \u2191" if self._sort_asc else " \u2193"
            table.columns[col_key].label = label
        table.refresh()

    # ── filter events ────────────────────────────────────────────

    @on(Select.Changed, "#sel-filter-status")
    def on_status_filter(self, event: Select.Changed) -> None:
        val = event.value
        if val == Select.BLANK or not isinstance(val, str) or val == "all":
            self.filter_status = None
        else:
            self.filter_status = Status(val)
        self.page = 0
        self._refresh_table()

    @on(Select.Changed, "#sel-filter-category")
    def on_category_filter(self, event: Select.Changed) -> None:
        val = event.value
        if val == Select.BLANK or not isinstance(val, str) or val == "all":
            self.filter_category = None
        else:
            self.filter_category = val
        self.page = 0
        self._refresh_table()

    # ── actions ──────────────────────────────────────────────────

    def action_add_item(self) -> None:
        def on_result(result: Optional[BacklogItem]) -> None:
            if result is not None:
                self.repo.create(result)
                self._refresh_categories()
                self._refresh_table()
                self.notify("Item added")

        self.push_screen(ItemFormScreen(categories=self.repo.get_categories()), callback=on_result)

    def action_edit_item(self) -> None:
        item_id = self._selected_item_id()
        if item_id is None:
            self.notify("No item selected", severity="warning")
            return
        item = self.repo.get(item_id)
        if item is None:
            return
        original_status = item.status

        def on_result(result: Optional[BacklogItem]) -> None:
            if result is not None:
                self.repo.update(
                    item_id,
                    title=result.title,
                    description=result.description,
                    category=result.category,
                    priority=result.priority,
                )
                if result.status != original_status:
                    try:
                        self.repo.transition_status(item_id, result.status)
                    except ValueError as exc:
                        self._refresh_categories()
                        self._refresh_table()
                        self.notify(str(exc), severity="error")
                        return
                self._refresh_categories()
                self._refresh_table()
                self.notify("Item updated")

        self.push_screen(ItemFormScreen(item, categories=self.repo.get_categories()), callback=on_result)

    def action_delete_item(self) -> None:
        item_id = self._selected_item_id()
        if item_id is None:
            self.notify("No item selected", severity="warning")
            return
        item = self.repo.get(item_id)
        if item is None:
            return

        def on_confirmed(confirmed: bool) -> None:
            if confirmed:
                success = self.repo.delete(item_id)
                self._refresh_table()
                if success:
                    self.notify("Item moved to trash")
                else:
                    self.notify("Delete failed", severity="error")

        self.push_screen(ConfirmDeleteScreen(item.title), callback=on_confirmed)

    def action_open_trash(self) -> None:
        def on_closed(result: None) -> None:
            self._refresh_table()

        self.push_screen(TrashScreen(self.repo), callback=on_closed)

    def action_toggle_status(self) -> None:
        item_id = self._selected_item_id()
        if item_id is None:
            self.notify("No item selected", severity="warning")
            return
        item = self.repo.get(item_id)
        if item is None:
            return
        next_s = NEXT_STATUS[item.status]
        try:
            self.repo.transition_status(item_id, next_s)
            self._refresh_table()
            self.notify(f"Status -> {next_s.value.replace('_', ' ').capitalize()}")
        except ValueError as exc:
            self.notify(str(exc), severity="error")

    def action_search(self) -> None:
        def on_result(result: Optional[str]) -> None:
            if result is not None:
                self.filter_keyword = result if result else None
                self.page = 0
                self._refresh_table()
                if result:
                    self.notify(f"Filter: '{result}'")
                else:
                    self.notify("Filter cleared")

        self.push_screen(SearchScreen(), callback=on_result)

    def action_next_page(self) -> None:
        total_pages = max(1, (self._total_count + self.page_size - 1) // self.page_size)
        if self.page < total_pages - 1:
            self.page += 1
            self._refresh_table()
        else:
            self.notify("Already on last page", severity="warning")

    def action_prev_page(self) -> None:
        if self.page > 0:
            self.page -= 1
            self._refresh_table()
        else:
            self.notify("Already on first page", severity="warning")

    def action_export_data(self) -> None:
        self.push_screen(ExportScreen(self.repo))

    def action_import_data(self) -> None:
        def on_closed(imported: bool) -> None:
            if imported:
                self._refresh_categories()
                self._refresh_table()

        self.push_screen(ImportScreen(self.repo), callback=on_closed)

    def action_show_versions(self) -> None:
        self.push_screen(VersionScreen())

    def action_help(self) -> None:
        self.push_screen(HelpScreen())


if __name__ == "__main__":
    BacklogApp().run()
```

- [ ] **Step 6: Update `tests/test_app_v080.py`**

Remove all `CATEGORY_COLORS` and `category_color` imports and tests. The file tests CSS values in `item_form.py` which are still valid, so keep those. Replace contents:

```python
"""Tests for v0.8.0 changes: CSS numeric values in item_form.py."""

import re
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ── CSS numeric values ────────────────────────────────────────────────────────

def _read_source(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


ITEM_FORM_PY = os.path.join(os.path.dirname(__file__), "..", "src", "screens", "item_form.py")
_SOURCE = _read_source(ITEM_FORM_PY)


class TestCssFormContainerWidth(unittest.TestCase):
    """#form-container width must be 84 (v0.8.0 changed from 70)."""

    def test_form_container_width_is_84(self):
        m = re.search(
            r"#form-container\s*\{[^}]*width\s*:\s*(\d+)\s*;",
            _SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "#form-container CSS block not found")
        self.assertEqual(int(m.group(1)), 84)


class TestCssInpDescHeight(unittest.TestCase):
    """#inp-desc height must be 9 (v0.8.0 changed from 7)."""

    def test_inp_desc_height_is_9(self):
        m = re.search(
            r"#inp-desc\s*\{[^}]*height\s*:\s*(\d+)\s*;",
            _SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "#inp-desc CSS block not found")
        self.assertEqual(int(m.group(1)), 9)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 7: Run all tests**

Run: `cd /root/yanay/codes/backlog/.worktrees/v0.9.0 && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git rm src/themes.py src/screens/theme_screen.py
git add src/app.py src/config.py src/screens/__init__.py src/screens/help_screen.py tests/test_v090.py tests/test_app_v080.py
git commit -m "refactor: remove theme system, wire ColorConfig into app"
```
