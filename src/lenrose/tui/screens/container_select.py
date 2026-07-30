"""Container selection screen with checkmarks and per-container result limits."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Header, Input, Label, Static

from lenrose.state.models import SelectedContainer
from lenrose.tiled_client.introspect import list_containers


class ContainerSelectScreen(Screen):
    """Select which containers to ingest and how many records from each."""

    CSS = """
    VerticalScroll { padding: 1 2; height: 1fr; }
    .row { height: auto; }
    Input.limit { width: 12; }
    #status { color: $warning; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Select containers to ingest")
            yield VerticalScroll(id="list")
            yield Static("", id="status")
            with Horizontal():
                yield Button("Discover keys", variant="primary", id="next")

    def on_mount(self) -> None:
        status = self.query_one("#status", Static)
        try:
            containers = list_containers(self.app.ctx.client)
        except Exception as exc:
            status.update(f"Failed to list containers: {exc}")
            return
        self.app.ctx.containers = containers
        listing = self.query_one("#list", VerticalScroll)
        for c in containers:
            count = f" ({c.count})" if c.count is not None else ""
            row = Horizontal(classes="row")
            listing.mount(row)
            row.mount(Checkbox(f"{c.path}{count}", value=False, id=f"cb-{c.path}"))
            row.mount(Input(value="100", classes="limit", id=f"limit-{c.path}"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "next":
            return
        selected: list[SelectedContainer] = []
        for c in self.app.ctx.containers:
            cb = self.query_one(f"#cb-{c.path}", Checkbox)
            if not cb.value:
                continue
            limit_widget = self.query_one(f"#limit-{c.path}", Input)
            try:
                limit = int(limit_widget.value)
            except ValueError:
                limit = 100
            selected.append(SelectedContainer(path=c.path, result_limit=limit))

        status = self.query_one("#status", Static)
        if not selected:
            status.update("Select at least one container.")
            return
        self.app.ctx.selected_containers = selected
        self.app.push_key_select()
