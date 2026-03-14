"""SearchScreen - modal for entering a search keyword."""

from __future__ import annotations

from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label


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
