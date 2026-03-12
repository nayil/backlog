"""Backlog Manager TUI application using Textual."""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import io_service

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from textual.theme import Theme
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListView,
    ListItem,
    Select,
    Static,
)

# Ensure src/ is on the path so models/repository can be imported directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import BacklogConfig, get_theme, set_theme
from models import BacklogItem, Priority, Status
from repository import BacklogRepository

DB_PATH = os.path.join(Path.home(), ".backlog", "backlog.db")

# ── helpers ──────────────────────────────────────────────────────────

STATUS_DISPLAY = {
    Status.TODO: "📋 Todo",
    Status.IN_PROGRESS: "🔨 In Progress",
    Status.DONE: "✅ Done",
}

PRIORITY_DISPLAY = {
    Priority.HIGH: "🔴 High",
    Priority.MEDIUM: "🟡 Medium",
    Priority.LOW: "🟢 Low",
}

NEXT_STATUS = {
    Status.TODO: Status.IN_PROGRESS,
    Status.IN_PROGRESS: Status.DONE,
    Status.DONE: Status.IN_PROGRESS,
}


# ── Item Form Screen ────────────────────────────────────────────────


class ItemFormScreen(ModalScreen[Optional[BacklogItem]]):
    """Modal dialog for creating / editing a backlog item."""

    CSS = """
    ItemFormScreen {
        align: center middle;
    }
    #form-container {
        width: 70;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #form-container Label {
        margin-top: 1;
    }
    #form-container Input, #form-container Select {
        width: 100%;
    }
    #form-buttons {
        margin-top: 1;
        height: 3;
        align: center middle;
    }
    #form-buttons Static {
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Save"),
    ]

    def __init__(self, item: Optional[BacklogItem] = None, categories: list[str] | None = None) -> None:
        super().__init__()
        self.item = item
        self._categories = categories or []

    def compose(self) -> ComposeResult:
        title = "Edit Item" if self.item else "New Item"
        with Vertical(id="form-container"):
            yield Label(f"[bold]{title}[/bold]")

            yield Label("Title")
            yield Input(
                value=self.item.title if self.item else "",
                placeholder="Item title",
                id="inp-title",
            )

            yield Label("Description")
            yield Input(
                value=self.item.description if self.item else "",
                placeholder="Description (optional)",
                id="inp-desc",
            )

            yield Label("Category")
            yield Input(
                value=self.item.category if self.item else "",
                placeholder="Category (optional)",
                id="inp-category",
                suggester=SuggestFromList(self._categories, case_sensitive=False) if self._categories else None,
            )

            yield Label("Priority")
            yield Select(
                [(p.value.capitalize(), p.value) for p in Priority],
                value=(self.item.priority.value if self.item else Priority.MEDIUM.value),
                id="sel-priority",
            )

            if self.item:
                yield Label("Status")
                yield Select(
                    [(s.value.replace("_", " ").capitalize(), s.value) for s in Status],
                    value=self.item.status.value,
                    id="sel-status",
                )

            with Horizontal(id="form-buttons"):
                yield Static("[bold][Ctrl+S][/bold] Save  |  [bold][Esc][/bold] Cancel")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        title = self.query_one("#inp-title", Input).value.strip()
        if not title:
            self.notify("Title is required", severity="error")
            return

        desc = self.query_one("#inp-desc", Input).value.strip()
        category = self.query_one("#inp-category", Input).value.strip()
        priority = Priority(self.query_one("#sel-priority", Select).value)

        if self.item:
            status_sel = self.query_one("#sel-status", Select)
            status = Status(status_sel.value)
            self.item.title = title
            self.item.description = desc
            self.item.category = category
            self.item.priority = priority
            self.item.status = status
            self.dismiss(self.item)
        else:
            new_item = BacklogItem(
                title=title,
                description=desc,
                category=category,
                priority=priority,
            )
            self.dismiss(new_item)


# ── Search Screen ───────────────────────────────────────────────────


class SearchScreen(ModalScreen[Optional[str]]):
    """Modal for entering a search keyword."""

    CSS = """
    SearchScreen { align: center middle; }
    #search-box {
        width: 60;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="search-box"):
            yield Label("[bold]Search[/bold]")
            yield Input(placeholder="Enter keyword (empty = clear filter)", id="inp-search")

    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Input.Submitted, "#inp-search")
    def on_submit(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.dismiss(value if value else "")


# ── Confirm Delete Screen ───────────────────────────────────────────


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Modal dialog asking the user to confirm a delete action."""

    CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }
    #confirm-container {
        width: 60;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    #confirm-container Label {
        margin-top: 1;
    }
    #confirm-buttons {
        margin-top: 1;
        height: 3;
        align: center middle;
    }
    #confirm-buttons Static {
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("enter", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "No"),
    ]

    def __init__(self, item_title: str, permanent: bool = False) -> None:
        super().__init__()
        self.item_title = item_title
        self.permanent = permanent

    def compose(self) -> ComposeResult:
        if self.permanent:
            title = "[bold]Delete Forever?[/bold]"
            message = "This action cannot be undone."
        else:
            title = "[bold]Move to Trash?[/bold]"
            message = "The item will be moved to trash and can be restored within 180 days."
        with Vertical(id="confirm-container"):
            yield Label(title)
            yield Label(f"Item: [italic]{self.item_title}[/italic]")
            yield Label(message)
            with Horizontal(id="confirm-buttons"):
                yield Static("[bold][Y/Enter][/bold] Yes  |  [bold][N/Esc][/bold] No")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


# ── Trash Screen ─────────────────────────────────────────────────────


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

    def __init__(self, repo: BacklogRepository) -> None:
        super().__init__()
        self.repo = repo
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
        table.add_columns("ID", "Title", "Category", "Deleted At", "Expires At")
        self._refresh_trash()

    def _refresh_trash(self) -> None:
        keyword = self.search_keyword
        table = self.query_one("#trash-table", DataTable)
        table.clear()
        items = self.repo.list_trash(
            keyword=keyword,
            limit=self.page_size,
            offset=self.page * self.page_size,
        )
        for item in items:
            deleted_str = item.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if item.deleted_at else "-"
            expires_str = item.expires_at.strftime("%Y-%m-%d") if item.expires_at else "-"
            table.add_row(
                str(item.id),
                item.title,
                item.category or "-",
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


# ── Help Screen ──────────────────────────────────────────────────────


class HelpScreen(ModalScreen[None]):
    """Modal screen displaying keyboard shortcuts and feature descriptions."""

    CSS = """
    HelpScreen {
        align: center middle;
    }
    #help-container {
        width: 60;
        height: auto;
        max-height: 85%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #help-container Label {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_help", "Close"),
        Binding("q", "dismiss_help", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Label("[bold]Backlog Manager — Keyboard Shortcuts[/bold]")
            yield Label("─" * 43)
            yield Label("[bold] Navigation[/bold]")
            yield Label("   ↑ / ↓          Move cursor between items")
            yield Label("   n              Next page")
            yield Label("   p              Previous page")
            yield Label("")
            yield Label("[bold] Item Management[/bold]")
            yield Label("   a              Add a new item")
            yield Label("   e              Edit selected item")
            yield Label("   d              Delete selected item (moves to Trash)")
            yield Label("   s              Toggle status: Todo → In Progress → Done → In Progress")
            yield Label("")
            yield Label("[bold] Filters[/bold]")
            yield Label("   /              Open search / filter by keyword")
            yield Label("   (Status & Category dropdowns at top)")
            yield Label("")
            yield Label("[bold] Trash[/bold]")
            yield Label("   t              Open Trash bin")
            yield Label("   r (in Trash)   Restore selected item")
            yield Label("   x (in Trash)   Permanently delete selected item")
            yield Label("   / (in Trash)   Search trash items")
            yield Label("")
            yield Label("[bold] Import / Export[/bold]")
            yield Label("   Ctrl+E         Export data to JSON or CSV file")
            yield Label("   Ctrl+O         Import data from JSON or CSV file")
            yield Label("")
            yield Label("[bold] Other[/bold]")
            yield Label("   v              Show version history")
            yield Label("   Ctrl+T         Switch color theme")
            yield Label("   ?              Show this help")
            yield Label("   q              Quit")
            yield Label("─" * 43)
            yield Label("Press [bold][Esc][/bold] or [bold][Q][/bold] to close")

    def action_dismiss_help(self) -> None:
        self.dismiss(None)


# ── Version Screen ───────────────────────────────────────────────────


class VersionScreen(ModalScreen[None]):
    """Modal screen displaying available historical versions from the release/ directory."""

    CSS = """
    VersionScreen {
        align: center middle;
    }
    #version-container {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #version-container Label {
        margin-bottom: 1;
    }
    """

    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]

    def _get_release_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent / "release"

    def _parse_versions(self) -> list[str]:
        release_dir = self._get_release_dir()
        if not release_dir.exists():
            return []
        versions: set[str] = set()
        for f in release_dir.iterdir():
            match = re.search(r"v\d+\.\d+\.\d+", f.name)
            if match:
                versions.add(match.group(0))
        return sorted(
            versions,
            key=lambda v: tuple(int(x) for x in v[1:].split(".")),
            reverse=True,
        )

    def compose(self) -> ComposeResult:
        with Vertical(id="version-container"):
            yield Label("[bold]📦 Available Versions[/bold]")
            yield DataTable(id="version-table")
            yield Static("[bold][Esc][/bold] Close")

    def on_mount(self) -> None:
        table = self.query_one("#version-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("#", "Version")
        versions = self._parse_versions()
        if versions:
            for idx, ver in enumerate(versions, start=1):
                table.add_row(str(idx), ver)
        else:
            table.add_row("-", "(no releases found)")

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)


# ── Export Screen ────────────────────────────────────────────────────


class ExportScreen(ModalScreen[None]):
    """Modal dialog for exporting backlog data to JSON or CSV."""

    CSS = """
    ExportScreen {
        align: center middle;
    }
    #export-container {
        width: 70;
        height: auto;
        max-height: 80%;
        border: thick $success;
        background: $surface;
        padding: 1 2;
    }
    #export-container Label {
        margin-top: 1;
    }
    #export-container Input, #export-container Select {
        width: 100%;
    }
    #export-buttons {
        margin-top: 1;
        height: 3;
        align: center middle;
    }
    #export-buttons Static {
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Export"),
    ]

    def __init__(self, repo: BacklogRepository) -> None:
        super().__init__()
        self.repo = repo

    def compose(self) -> ComposeResult:
        with Vertical(id="export-container"):
            yield Label("[bold]📤 Export Data[/bold]")

            yield Label("Format")
            yield Select(
                [("JSON (.json)", "json"), ("CSV (.csv)", "csv")],
                value="json",
                id="sel-export-format",
            )

            yield Label("File Path")
            yield Input(
                value=str(Path.home() / "backlog-export.json"),
                placeholder="Export file path",
                id="inp-export-path",
            )

            with Horizontal(id="export-buttons"):
                yield Static("[bold][Ctrl+S][/bold] Export  |  [bold][Esc][/bold] Cancel")

    @on(Select.Changed, "#sel-export-format")
    def on_format_changed(self, event: Select.Changed) -> None:
        fmt = event.value
        path_input = self.query_one("#inp-export-path", Input)
        current = path_input.value
        if fmt == "csv":
            if current.endswith(".json"):
                path_input.value = current[:-5] + ".csv"
            elif not current.endswith(".csv"):
                path_input.value = str(Path.home() / "backlog-export.csv")
        else:
            if current.endswith(".csv"):
                path_input.value = current[:-4] + ".json"
            elif not current.endswith(".json"):
                path_input.value = str(Path.home() / "backlog-export.json")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        fmt = self.query_one("#sel-export-format", Select).value
        file_path = self.query_one("#inp-export-path", Input).value.strip()

        if not file_path:
            self.notify("File path is required", severity="error")
            return

        items = self.repo.list()
        try:
            if fmt == "csv":
                count = io_service.export_csv(items, file_path)
            else:
                count = io_service.export_json(items, file_path)
            self.notify(f"Exported {count} item(s) to {file_path}")
            self.dismiss(None)
        except OSError as exc:
            self.notify(f"Export failed: {exc}", severity="error")
        except Exception as exc:
            self.notify(f"Unexpected error: {exc}", severity="error")


# ── Import Screen ────────────────────────────────────────────────────


class ImportScreen(ModalScreen[bool]):
    """Modal dialog for importing backlog data from JSON or CSV."""

    CSS = """
    ImportScreen {
        align: center middle;
    }
    #import-container {
        width: 70;
        height: auto;
        max-height: 80%;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }
    #import-container Label {
        margin-top: 1;
    }
    #import-container Input, #import-container Select {
        width: 100%;
    }
    #import-buttons {
        margin-top: 1;
        height: 3;
        align: center middle;
    }
    #import-buttons Static {
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Import"),
    ]

    def __init__(self, repo: BacklogRepository) -> None:
        super().__init__()
        self.repo = repo

    def compose(self) -> ComposeResult:
        with Vertical(id="import-container"):
            yield Label("[bold]📥 Import Data[/bold]")

            yield Label("Format")
            yield Select(
                [("JSON (.json)", "json"), ("CSV (.csv)", "csv")],
                value="json",
                id="sel-import-format",
            )

            yield Label("File Path")
            yield Input(
                placeholder="Path to file to import",
                id="inp-import-path",
            )

            yield Label(
                "[dim]Note: Records with empty title or deleted records will be skipped.[/dim]"
            )

            with Horizontal(id="import-buttons"):
                yield Static("[bold][Ctrl+S][/bold] Import  |  [bold][Esc][/bold] Cancel")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_submit(self) -> None:
        fmt = self.query_one("#sel-import-format", Select).value
        file_path = self.query_one("#inp-import-path", Input).value.strip()

        if not file_path:
            self.notify("File path is required", severity="error")
            return

        if not Path(file_path).exists():
            self.notify(f"File not found: {file_path}", severity="error")
            return

        try:
            if fmt == "csv":
                imported, skipped = io_service.import_csv(file_path, self.repo)
            else:
                imported, skipped = io_service.import_json(file_path, self.repo)
            msg = f"Imported {imported} item(s)"
            if skipped:
                msg += f", skipped {skipped}"
            self.notify(msg)
            self.dismiss(True)
        except (OSError, ValueError, KeyError) as exc:
            self.notify(f"Import failed: {exc}", severity="error")
        except Exception as exc:
            self.notify(f"Unexpected error: {exc}", severity="error")


# ── Theme Screen ─────────────────────────────────────────────────────

_THEME_BACKLOG_LIGHT = Theme(
    name="backlog-light",
    primary="#0066CC",
    secondary="#005599",
    accent="#E05C00",
    foreground="#1A1A2E",
    background="#F5F5F5",
    surface="#FFFFFF",
    panel="#E8E8EC",
    success="#2E8B57",
    warning="#CC7700",
    error="#CC2200",
    dark=False,
    variables={
        "block-cursor-foreground": "#FFFFFF",
        "block-cursor-background": "#0066CC",
        "footer-key-foreground": "#E05C00",
        "input-selection-background": "#0066CC 35%",
    },
)

_THEME_BACKLOG_NORD = Theme(
    name="backlog-nord",
    primary="#88C0D0",
    secondary="#81A1C1",
    accent="#EBCB8B",
    foreground="#ECEFF4",
    background="#2E3440",
    surface="#3B4252",
    panel="#434C5E",
    success="#A3BE8C",
    warning="#EBCB8B",
    error="#BF616A",
    dark=True,
    variables={
        "block-cursor-foreground": "#2E3440",
        "block-cursor-background": "#88C0D0",
        "footer-key-foreground": "#EBCB8B",
        "input-selection-background": "#81A1C1 40%",
    },
)

_THEME_BACKLOG_SOLARIZED_LIGHT = Theme(
    name="backlog-solarized-light",
    primary="#268BD2",
    secondary="#2AA198",
    accent="#CB4B16",
    foreground="#002B36",
    background="#FDF6E3",
    surface="#EEE8D5",
    panel="#DDD8C5",
    success="#2AA198",
    warning="#B58900",
    error="#DC322F",
    dark=False,
    variables={
        "block-cursor-foreground": "#FDF6E3",
        "block-cursor-background": "#268BD2",
        "footer-key-foreground": "#CB4B16",
        "input-selection-background": "#268BD2 30%",
    },
)

_THEME_BACKLOG_SOLARIZED_DARK = Theme(
    name="backlog-solarized-dark",
    primary="#268BD2",
    secondary="#2AA198",
    accent="#CB4B16",
    foreground="#EAE3CB",
    background="#002B36",
    surface="#073642",
    panel="#0D4450",
    success="#859900",
    warning="#B58900",
    error="#DC322F",
    dark=True,
    variables={
        "block-cursor-foreground": "#002B36",
        "block-cursor-background": "#268BD2",
        "footer-key-foreground": "#CB4B16",
        "input-selection-background": "#268BD2 35%",
    },
)

_THEME_BACKLOG_GRUVBOX = Theme(
    name="backlog-gruvbox",
    primary="#B8BB26",
    secondary="#8EC07C",
    accent="#FABD2F",
    foreground="#FBF1C7",
    background="#282828",
    surface="#3C3836",
    panel="#504945",
    success="#8EC07C",
    warning="#FABD2F",
    error="#FB4934",
    dark=True,
    variables={
        "block-cursor-foreground": "#282828",
        "block-cursor-background": "#B8BB26",
        "footer-key-foreground": "#FABD2F",
        "input-selection-background": "#689D6A 40%",
    },
)

_THEME_BACKLOG_DRACULA = Theme(
    name="backlog-dracula",
    primary="#BD93F9",
    secondary="#6272A4",
    accent="#FF79C6",
    foreground="#F8F8F2",
    background="#282A36",
    surface="#383A59",
    panel="#44475A",
    success="#50FA7B",
    warning="#FFB86C",
    error="#FF5555",
    dark=True,
    variables={
        "block-cursor-foreground": "#282A36",
        "block-cursor-background": "#BD93F9",
        "footer-key-foreground": "#FF79C6",
        "input-selection-background": "#6272A4 50%",
    },
)

CUSTOM_THEMES = [
    _THEME_BACKLOG_LIGHT,
    _THEME_BACKLOG_NORD,
    _THEME_BACKLOG_SOLARIZED_LIGHT,
    _THEME_BACKLOG_SOLARIZED_DARK,
    _THEME_BACKLOG_GRUVBOX,
    _THEME_BACKLOG_DRACULA,
]

AVAILABLE_THEMES: list[tuple[str, str]] = [
    ("textual-dark", "默认暗色"),
    ("backlog-light", "清爽亮色"),
    ("backlog-nord", "北欧冷蓝"),
    ("backlog-solarized-light", "Solarized 护眼暖白"),
    ("backlog-solarized-dark", "Solarized 护眼暗色"),
    ("backlog-gruvbox", "复古终端暖黄绿"),
    ("backlog-dracula", "流行紫色暗色"),
]


class ThemeScreen(ModalScreen[Optional[str]]):
    """Modal screen for theme selection with live preview."""

    CSS = """
    ThemeScreen {
        align: center middle;
    }
    #theme-container {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #theme-container Label {
        margin-bottom: 1;
    }
    #theme-list {
        height: auto;
        max-height: 20;
        border: solid $accent;
    }
    #theme-hint {
        margin-top: 1;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "confirm", "Apply"),
    ]

    def __init__(self, current_theme: str) -> None:
        super().__init__()
        self._current_theme = current_theme
        self._original_theme = current_theme

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-container"):
            yield Label("[bold]🎨 Select Theme[/bold]")
            items = [
                ListItem(Label(f"  {name}  —  {desc}"), id=f"theme-{name}")
                for name, desc in AVAILABLE_THEMES
            ]
            yield ListView(*items, id="theme-list")
            yield Static(
                "[bold][Enter][/bold] Apply  |  [bold][Esc][/bold] Cancel",
                id="theme-hint",
            )

    def on_mount(self) -> None:
        lv = self.query_one("#theme-list", ListView)
        theme_names = [name for name, _ in AVAILABLE_THEMES]
        if self._current_theme in theme_names:
            lv.index = theme_names.index(self._current_theme)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            item_id = event.item.id or ""
            if item_id.startswith("theme-"):
                theme_name = item_id[len("theme-"):]
                self.app.theme = theme_name
                self._current_theme = theme_name

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_confirm()

    def action_confirm(self) -> None:
        self.dismiss(self._current_theme)

    def action_cancel(self) -> None:
        self.app.theme = self._original_theme
        self.dismiss(None)


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
    DataTable {
        height: 1fr;
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
        Binding("ctrl+t", "change_theme", "Theme"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, db_path: str = DB_PATH) -> None:
        super().__init__()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.repo = BacklogRepository(db_path)
        self.config = BacklogConfig()
        self.filter_status: Optional[Status] = None
        self.filter_category: Optional[str] = None
        self.filter_keyword: Optional[str] = None
        self.page: int = 0
        self.page_size: int = 20
        self._total_count: int = 0

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
        yield DataTable(id="table")
        yield Static("", id="stats-bar")
        yield Footer()

    def on_mount(self) -> None:
        for theme in CUSTOM_THEMES:
            self.register_theme(theme)
        table = self.query_one("#table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Title", "Status", "Category", "Priority", "Age")
        self._refresh_categories()
        self._refresh_table()
        saved_theme = self.config.get_theme()
        if saved_theme in {name for name, _ in AVAILABLE_THEMES}:
            self.theme = saved_theme

    # ── data refresh ─────────────────────────────────────────────

    def _refresh_table(self) -> None:
        table = self.query_one("#table", DataTable)
        table.clear()
        items = self.repo.list(
            status=self.filter_status,
            category=self.filter_category,
            keyword=self.filter_keyword,
            limit=self.page_size,
            offset=self.page * self.page_size,
        )
        now = datetime.now()
        for item in items:
            age_str = f"{(now - item.created_at).days}d" if item.created_at else "-"
            table.add_row(
                str(item.id),
                item.title,
                STATUS_DISPLAY.get(item.status, item.status.value),
                item.category or "-",
                PRIORITY_DISPLAY.get(item.priority, item.priority.value),
                age_str,
                key=str(item.id),
            )
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
                # Update non-status fields directly
                self.repo.update(
                    item_id,
                    title=result.title,
                    description=result.description,
                    category=result.category,
                    priority=result.priority,
                )
                # Use transition_status for status changes to enforce validation
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
            self.notify(f"Status → {next_s.value.replace('_', ' ').capitalize()}")
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

    def action_change_theme(self) -> None:
        def on_result(chosen: Optional[str]) -> None:
            if chosen is not None:
                self.theme = chosen
                self.config.set_theme(chosen)
                self.notify(f"Theme: {chosen}")

        self.push_screen(ThemeScreen(self.theme), callback=on_result)


if __name__ == "__main__":
    BacklogApp().run()
