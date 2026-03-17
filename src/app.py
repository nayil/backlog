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
    ConfirmQuitScreen,
    TrashScreen,
    HelpScreen,
    VersionScreen,
    ExportScreen,
    ImportScreen,
)
from config import BacklogConfig
from display import truncate_title
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
        Binding("q", "request_quit", "Quit"),
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
        col_keys = table.add_columns("ID", "Category", "Title", "Status", "Priority", "Age")
        self._col_keys = {
            "ID": col_keys[0],
            "Category": col_keys[1],
            "Title": col_keys[2],
            "Status": col_keys[3],
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
                item.category or "-",
                truncate_title(item.title, self.config.get_title_truncate_length()),
                colorize_status(item.status, self.color_config),
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

        self.push_screen(TrashScreen(self.repo, self.config), callback=on_closed)

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

    def action_request_quit(self) -> None:
        def on_confirmed(confirmed: bool) -> None:
            if confirmed:
                self.exit()

        self.push_screen(ConfirmQuitScreen(), callback=on_confirmed)

    def action_help(self) -> None:
        self.push_screen(HelpScreen())


if __name__ == "__main__":
    if "--version" in sys.argv:
        try:
            from __init__ import __version__
        except ImportError:
            __version__ = "1.0.0"
        print(f"backlog {__version__}")
        sys.exit(0)
    BacklogApp().run()
