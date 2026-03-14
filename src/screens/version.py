"""VersionScreen — Modal screen displaying available historical versions."""

from __future__ import annotations

import re
from pathlib import Path

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label, Static
from textual.app import ComposeResult


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
        return Path(__file__).resolve().parent.parent.parent / "release"

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
