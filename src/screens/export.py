"""ExportScreen - Modal dialog for exporting backlog data to JSON or CSV."""

from __future__ import annotations

from pathlib import Path

import io_service

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Select, Static

from repository import BacklogRepository


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
