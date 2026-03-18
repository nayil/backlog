"""Backlog Manager TUI application using Textual."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Select, Static

# Ensure src/ is on the path so models/repository can be imported directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from colors import NEXT_STATUS
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
from models import BacklogItem, Status
from repository import BacklogRepository
from widgets import FilterBar, MainTable, StatsBar, calc_total_pages, clamp_page

DB_PATH = os.path.join(Path.home(), ".backlog", "backlog.db")

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
        self.page_size: int = self.config.get_page_size()
        self._total_count: int = 0
        self._sort_by: Optional[str] = None
        self._sort_asc: bool = True

    def compose(self) -> ComposeResult:
        yield Header()
        self._filter_bar = FilterBar(
            categories=[],
            filter_status=self.filter_status,
            filter_category=self.filter_category,
            id="filter-bar",
        )
        yield self._filter_bar
        self._preview_title = Static("", id="preview-title")
        self._preview_desc = Static("", id="preview-desc")
        self._main_table = MainTable(
            self.repo,
            self.config,
            self.color_config,
            self._preview_title,
            self._preview_desc,
            on_sort_changed=self._on_sort_changed,
            id="table",
        )
        with Horizontal(id="main-content"):
            yield self._main_table
            with VerticalScroll(id="preview-panel"):
                yield self._preview_title
                yield self._preview_desc
        yield Footer()
        self._stats_bar = StatsBar(id="stats-bar")
        yield self._stats_bar

    def on_mount(self) -> None:
        self._refresh_categories()
        self._refresh_table()

    def _on_sort_changed(self, sort_by: Optional[str], sort_asc: bool) -> None:
        self._sort_by = sort_by
        self._sort_asc = sort_asc
        self.page = 0
        self._refresh_table()

    # ── data refresh ─────────────────────────────────────────────

    def _refresh_table(self) -> None:
        self._total_count = self.repo.count(
            status=self.filter_status,
            category=self.filter_category,
            keyword=self.filter_keyword,
        )
        total_pages = calc_total_pages(self._total_count, self.page_size)
        self.page = clamp_page(self.page, total_pages)
        self._main_table.refresh(
            filter_status=self.filter_status,
            filter_category=self.filter_category,
            filter_keyword=self.filter_keyword,
            page=self.page,
            page_size=self.page_size,
            sort_by=self._sort_by,
            sort_asc=self._sort_asc,
        )
        stats = self.repo.get_stats(category=self.filter_category)
        by_s = stats["by_status"]
        current_page = self.page + 1
        self._stats_bar.update_stats(
            self._total_count, by_s, current_page, total_pages
        )

    def _refresh_categories(self) -> None:
        self._filter_bar.set_categories(self.repo.get_categories())

    def _selected_item_id(self) -> Optional[int]:
        return self._main_table.selected_item_id

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
        total_pages = calc_total_pages(self._total_count, self.page_size)
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
