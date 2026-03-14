"""ImportScreen - Modal dialog for importing backlog data from JSON or CSV."""

from __future__ import annotations

from pathlib import Path

import io_service

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Select, Static

from repository import BacklogRepository


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
