"""HelpScreen — Modal screen displaying keyboard shortcuts and feature descriptions."""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Label
from textual.app import ComposeResult

from color_config import ColorConfig
from config import BacklogConfig


class HelpScreen(ModalScreen[None]):
    """Modal screen displaying keyboard shortcuts and feature descriptions."""

    CSS = """
    HelpScreen {
        align: center middle;
    }
    #help-container {
        width: 60;
        height: auto;
        max-height: 90%;
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
        with VerticalScroll(id="help-container"):
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
            yield Label("                  (Edit form: set any status)")
            yield Label("   d              Delete selected item (moves to Trash)")
            yield Label("   s              Cycle: Todo → InProg → Done → InProg")
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
            yield Label("   (Deleted items auto-expire after 180 days)")
            yield Label("")
            yield Label("[bold] Import / Export[/bold]")
            yield Label("   Ctrl+E         Export data to JSON or CSV file")
            yield Label("   Ctrl+O         Import data from JSON or CSV file")
            yield Label("")
            yield Label("[bold] Other[/bold]")
            yield Label("   v              Show version history")
            yield Label("   ?              Show this help")
            yield Label("   q              Quit (with confirmation)")
            yield Label("")
            yield Label("[bold] Status Bar (bottom)[/bold]")
            yield Label("   Shows totals by status and current page / total pages")
            yield Label("")
            yield Label("[bold] Main List Columns[/bold]")
            yield Label("   ID             Unique item identifier")
            yield Label("   Title          Item title (category:description)")
            yield Label("   Status         Todo / In Progress / Done")
            yield Label("   Category       Item category (from title prefix)")
            yield Label("   Priority       High / Medium / Low")
            yield Label("   Age            Days since creation")
            yield Label("")
            yield Label("[bold] Item Form Fields[/bold]")
            yield Label("   Title          Required; format: category:description")
            yield Label("   Description    Optional free-text notes")
            yield Label("   Category       Optional; auto-suggests from existing")
            yield Label("   Priority       High / Medium (default) / Low")
            yield Label("   Status         Edit mode only; any value allowed")
            yield Label("")
            yield Label("[bold] Configuration[/bold]")
            yield Label("   Config file: ~/.backlog/config.json")
            yield Label("")
            yield Label("   [bold]title_truncate_length[/bold] — Max chars for Title column in list")
            yield Label(f"     Default: {BacklogConfig.DEFAULT_TITLE_TRUNCATE_LENGTH}; overflow shown as …")
            yield Label("")
            yield Label("   [bold]status_colors[/bold] — Status column colors")
            for key, val in ColorConfig.DEFAULT_STATUS_COLORS.items():
                yield Label(f"     {key:15s} {val}")
            yield Label("")
            yield Label("   [bold]priority_colors[/bold] — Priority column colors")
            for key, val in ColorConfig.DEFAULT_PRIORITY_COLORS.items():
                yield Label(f"     {key:15s} {val}")
            yield Label("")
            yield Label("─" * 43)
            yield Label("Press [bold][Esc][/bold] or [bold][Q][/bold] to close")

    def action_dismiss_help(self) -> None:
        self.dismiss(None)
