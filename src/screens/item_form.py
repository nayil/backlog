"""ItemFormScreen - modal dialog for creating / editing a backlog item."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from textual.widgets import Input, Label, Select, Static, TextArea

from models import BacklogItem, Priority, Status
from screens.confirm_discard import ConfirmDiscardScreen


class ItemFormScreen(ModalScreen[Optional[BacklogItem]]):
    """Modal dialog for creating / editing a backlog item."""

    CSS = """
    ItemFormScreen {
        align: center middle;
    }
    #form-container {
        width: 84;
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
    #inp-desc {
        height: 9;
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
            yield TextArea(
                self.item.description if self.item else "",
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

    def _has_changes(self) -> bool:
        """Return True if form has unsaved changes compared to initial state."""
        title = self.query_one("#inp-title", Input).value.strip()
        desc = self.query_one("#inp-desc", TextArea).text.strip()
        category = self.query_one("#inp-category", Input).value.strip()
        priority = Priority(self.query_one("#sel-priority", Select).value)

        if self.item is None:
            # New mode: any non-empty or priority != MEDIUM
            return bool(title or desc or category or priority != Priority.MEDIUM)

        # Edit mode: any field different from initial item
        if title != (self.item.title or "").strip():
            return True
        if desc != (self.item.description or "").strip():
            return True
        if category != (self.item.category or "").strip():
            return True
        if priority != self.item.priority:
            return True
        status_sel = self.query_one("#sel-status", Select)
        if Status(status_sel.value) != self.item.status:
            return True
        return False

    def action_cancel(self) -> None:
        if not self._has_changes():
            self.dismiss(None)
            return

        def on_discard_result(confirmed: bool) -> None:
            if confirmed:
                self.dismiss(None)

        self.push_screen(ConfirmDiscardScreen(), callback=on_discard_result)

    def action_submit(self) -> None:
        title = self.query_one("#inp-title", Input).value.strip()
        if not title:
            self.notify("Title is required", severity="error")
            return

        desc = self.query_one("#inp-desc", TextArea).text.strip()
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
