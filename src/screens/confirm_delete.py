"""ConfirmDeleteScreen - modal dialog for confirming a delete action."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, Static


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
