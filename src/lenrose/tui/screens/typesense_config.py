"""Typesense configuration screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Label, Select, Static


class TypesenseConfigScreen(Screen):
    """Gather Typesense connection details before connecting to Tiled."""

    CSS = """
    Vertical { padding: 1 2; }
    Input, Select { margin: 1 0; }
    #status { color: $error; }
    """

    def compose(self) -> ComposeResult:
        settings = self.app.ctx.settings

        yield Header()
        with Vertical():
            yield Label("Configure Typesense")
            yield Input(
                placeholder="localhost",
                value=settings.typesense_host,
                id="host",
            )
            yield Input(
                placeholder="8108",
                value=str(settings.typesense_port),
                id="port",
            )
            yield Select(
                [("http", "http"), ("https", "https")],
                value=settings.typesense_protocol,
                id="protocol",
            )
            yield Input(
                placeholder="API key",
                value=settings.typesense_api_key,
                id="api_key",
                password=True,
            )
            yield Button("Continue to Tiled", variant="primary", id="continue")
            yield Static("", id="status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "continue":
            return

        status = self.query_one("#status", Static)
        host = self.query_one("#host", Input).value.strip()
        port_value = self.query_one("#port", Input).value.strip()
        protocol = self.query_one("#protocol", Select).value
        api_key = self.query_one("#api_key", Input).value

        if not host:
            status.update("Please enter a Typesense host.")
            return
        try:
            port = int(port_value)
        except ValueError:
            status.update("Typesense port must be a number.")
            return
        if port <= 0:
            status.update("Typesense port must be positive.")
            return
        if protocol not in {"http", "https"}:
            status.update("Typesense protocol must be http or https.")
            return
        if not api_key:
            status.update("Please enter a Typesense API key.")
            return

        settings = self.app.ctx.settings
        settings.typesense_host = host
        settings.typesense_port = port
        settings.typesense_protocol = str(protocol)
        settings.typesense_api_key = api_key

        self.app.push_tiled_connect()
