"""ConfirmQuitScreen - modal dialog for confirming application quit."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, Static


class ConfirmQuitScreen(ModalScreen[bool]):
    """Modal dialog asking the user to confirm quitting the application."""

    CSS = """
    ConfirmQuitScreen {
        align: center middle;
    }
    #quit-confirm-container {
        width: 50;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #quit-confirm-container Label {
        margin-top: 1;
    }
    #quit-confirm-buttons {
        margin-top: 1;
        height: 3;
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("enter", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "No"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="quit-confirm-container"):
            yield Label("[bold]Quit Backlog Manager?[/bold]")
            with Horizontal(id="quit-confirm-buttons"):
                yield Static("[bold][Y/Enter][/bold] Yes  |  [bold][N/Esc][/bold] No")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
