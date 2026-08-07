"""Lenrose interactive ingestion TUI (Textual)."""

from __future__ import annotations

from textual.app import App

from lenrose.state.models import SelectedContainer
from lenrose.tiled_client.introspect import ROOT_PATH, has_nested_containers
from lenrose.tui.context import IngestContext
from lenrose.tui.screens.connect import ConnectScreen
from lenrose.tui.screens.container_select import ContainerSelectScreen
from lenrose.tui.screens.index_progress import IndexProgressScreen
from lenrose.tui.screens.key_select import KeySelectScreen
from lenrose.tui.screens.typesense_config import TypesenseConfigScreen


class LenroseApp(App):
    """Drives connect -> select containers -> select keys -> index."""

    TITLE = "Lenrose"
    SUB_TITLE = "Scientific Metadata Search Engine"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        self.ctx = IngestContext()
        # Set True only when the user completes the index build and presses
        # "Done". Quitting early (``q``) leaves this False so the unified
        # launcher knows not to start the server.
        self.setup_completed = False

    def on_mount(self) -> None:
        self.push_screen(TypesenseConfigScreen())

    def push_tiled_connect(self) -> None:
        self.push_screen(ConnectScreen())

    def push_container_select(self) -> None:
        # When the server holds all records directly in the root container
        # (no nested containers), skip container selection entirely and go
        # straight to key discovery using the root as a single container.
        try:
            nested = has_nested_containers(self.ctx.client)
        except Exception:
            nested = True
        if not nested:
            self.ctx.selected_containers = [
                SelectedContainer(path=ROOT_PATH, result_limit=100)
            ]
            self.push_key_select()
            return
        self.push_screen(ContainerSelectScreen())

    def push_key_select(self) -> None:
        self.push_screen(KeySelectScreen())

    def push_index_progress(self) -> None:
        self.push_screen(IndexProgressScreen())


def run() -> bool:
    """Run the setup TUI. Return True if setup completed successfully."""
    app = LenroseApp()
    app.run()
    return app.setup_completed


if __name__ == "__main__":
    run()
