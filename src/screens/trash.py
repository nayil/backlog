"""TrashScreen — Modal screen listing soft-deleted items with restore/hard-delete actions."""

from __future__ import annotations

from typing import Optional

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label, Static
from textual.app import ComposeResult

from config import BacklogConfig
from display import truncate_title
from repository import BacklogRepository
from screens.confirm_delete import ConfirmDeleteScreen
from screens.search import SearchScreen


class TrashScreen(ModalScreen[None]):
    """Modal screen listing soft-deleted items with restore/hard-delete actions."""

    CSS = """
    TrashScreen {
        align: center middle;
    }
    #trash-container {
        width: 90%;
        height: 80%;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }
    #trash-container Label {
        margin-bottom: 1;
    }
    #trash-hint {
        height: 1;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("r", "restore_item", "Restore"),
        Binding("x", "hard_delete_item", "Delete Forever"),
        Binding("slash", "search_trash", "Search"),
        Binding("n", "next_page", "Next Page"),
        Binding("p", "prev_page", "Prev Page"),
        Binding("escape", "dismiss_screen", "Close"),
    ]

    def __init__(
        self,
        repo: BacklogRepository,
        config: BacklogConfig | None = None,
    ) -> None:
        super().__init__()
        self.repo = repo
        self.config = config if config is not None else BacklogConfig()
        self.page: int = 0
        self.page_size: int = 20
        self.search_keyword: Optional[str] = None
        self._total_count: int = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="trash-container"):
            yield Label("[bold]🗑  Trash[/bold]")
            yield DataTable(id="trash-table")
            yield Static(
                "[bold][R][/bold] Restore  |  [bold][X][/bold] Delete Forever  |  [bold][Esc][/bold] Close",
                id="trash-hint",
            )

    def on_mount(self) -> None:
        table = self.query_one("#trash-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Category", "Title", "Deleted At", "Expires At")
        self._refresh_trash()

    def _refresh_trash(self) -> None:
        keyword = self.search_keyword
        table = self.query_one("#trash-table", DataTable)
        table.clear()
        table.move_cursor(row=0, animate=False)
        items = self.repo.list_trash(
            keyword=keyword,
            limit=self.page_size,
            offset=self.page * self.page_size,
        )
        max_len = self.config.get_title_truncate_length()
        for item in items:
            deleted_str = item.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if item.deleted_at else "-"
            expires_str = item.expires_at.strftime("%Y-%m-%d") if item.expires_at else "-"
            table.add_row(
                str(item.id),
                item.category or "-",
                truncate_title(item.title, max_len),
                deleted_str,
                expires_str,
                key=str(item.id),
            )
        total = self.repo.count_trash(keyword=keyword)
        self._total_count = total
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        current_page = self.page + 1
        hint = self.query_one("#trash-hint", Static)
        hint.update(
            f"[bold][R][/bold] Restore  |  [bold][X][/bold] Delete Forever  |  [bold]\\[/][/bold] Search  |  [bold][Esc][/bold] Close"
            f"  |  Page {current_page}/{total_pages}  [bold][N][/bold] Next  [bold][P][/bold] Prev"
        )

    def _selected_item_id(self) -> Optional[int]:
        table = self.query_one("#trash-table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            return int(row_key.value)
        except Exception:
            return None

    def action_restore_item(self) -> None:
        item_id = self._selected_item_id()
        if item_id is None:
            self.notify("No item selected", severity="warning")
            return
        restored = self.repo.restore(item_id)
        if restored:
            self.notify(f"Restored: {restored.title}")
            total = self.repo.count_trash(keyword=self.search_keyword)
            total_pages = max(1, (total + self.page_size - 1) // self.page_size)
            if self.page >= total_pages:
                self.page = max(0, total_pages - 1)
            self._refresh_trash()
        else:
            self.notify("Restore failed", severity="error")

    def action_hard_delete_item(self) -> None:
        item_id = self._selected_item_id()
        if item_id is None:
            self.notify("No item selected", severity="warning")
            return
        item = self.repo.get(item_id, include_deleted=True)
        title = item.title if item else f"#{item_id}"

        def on_confirmed(confirmed: bool) -> None:
            if confirmed:
                success = self.repo.hard_delete(item_id)
                if success:
                    self.notify(f"Permanently deleted: {title}")
                    total = self.repo.count_trash(keyword=self.search_keyword)
                    total_pages = max(1, (total + self.page_size - 1) // self.page_size)
                    if self.page >= total_pages:
                        self.page = max(0, total_pages - 1)
                    self._refresh_trash()
                else:
                    self.notify("Delete failed", severity="error")

        self.app.push_screen(ConfirmDeleteScreen(title, permanent=True), callback=on_confirmed)

    def action_search_trash(self) -> None:
        def on_result(result: Optional[str]) -> None:
            if result is not None:
                self.search_keyword = result if result else None
                self.page = 0
                self._refresh_trash()
                if result:
                    self.notify(f"Filter: '{result}'")
                else:
                    self.notify("Filter cleared")

        self.app.push_screen(SearchScreen(), callback=on_result)

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)

    def action_next_page(self) -> None:
        total_pages = max(1, (self._total_count + self.page_size - 1) // self.page_size)
        if self.page < total_pages - 1:
            self.page += 1
            self._refresh_trash()
        else:
            self.notify("Already on last page", severity="warning")

    def action_prev_page(self) -> None:
        if self.page > 0:
            self.page -= 1
            self._refresh_trash()
        else:
            self.notify("Already on first page", severity="warning")
