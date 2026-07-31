"""Key selection screen: discovered keys with facet/index/searchable toggles."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Header, Label, Static

from lenrose.schema.inference import parent_of
from lenrose.state.models import KeySpec
from lenrose.tiled_client.introspect import introspect_container


class KeySelectScreen(Screen):
    """Choose which metadata keys to index and their facet/index options."""

    CSS = """
    VerticalScroll { padding: 1 2; height: 1fr; }
    .row { height: auto; }
    .keyname { width: 40; }
    #status { color: $warning; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Select metadata keys to index (include / facet)")
            yield Static("collection is always indexed and faceted by default.")
            yield VerticalScroll(id="keys")
            yield Static("", id="status")
            with Horizontal():
                yield Button("Build index", variant="success", id="build")

    def on_mount(self) -> None:
        status = self.query_one("#status", Static)
        status.update("Discovering keys...")
        merged: dict[str, str] = {}
        try:
            for container in self.app.ctx.selected_containers:
                result = introspect_container(
                    self.app.ctx.client, container.path, container.result_limit
                )
                for dk in result.as_key_list():
                    if dk.dotted_key not in merged:
                        merged[dk.dotted_key] = dk.datatype
        except Exception as exc:
            status.update(f"Key discovery failed: {exc}")
            return

        status.update(f"Discovered {len(merged)} keys.")
        listing = self.query_one("#keys", VerticalScroll)
        # Textual widget IDs may contain only letters, numbers, underscores and
        # hyphens, so the dotted keys coming from Tiled (e.g.
        # ``start.BMM_motors.m1_pitch``) cannot be used directly. Assign each
        # key a stable positional slot and key the widgets off that slot,
        # keeping the real dotted key in ``self._slots`` for building specs.
        self._slots: dict[int, str] = {}
        for slot, (dotted, dtype) in enumerate(sorted(merged.items())):
            self._slots[slot] = dotted
            row = Horizontal(classes="row")
            listing.mount(row)
            row.mount(
                Checkbox(f"{dotted} [{dtype}]", value=True,
                         id=f"inc-{slot}", classes="keyname")
            )
            row.mount(Checkbox("facet", value=False, id=f"fac-{slot}"))
        self._discovered = merged

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "build":
            return
        specs: list[KeySpec] = []
        for slot, dotted in self._slots.items():
            dtype = self._discovered[dotted]
            inc = self.query_one(f"#inc-{slot}", Checkbox).value
            if not inc:
                continue
            fac = self.query_one(f"#fac-{slot}", Checkbox).value
            specs.append(
                KeySpec(
                    dotted_key=dotted,
                    parent=parent_of(dotted),
                    datatype=dtype,
                    is_facet=fac,
                    is_index=True,
                    is_searchable=dtype.startswith("string"),
                    is_system=False,
                    selected=True,
                )
            )
        self.app.ctx.key_specs = specs
        self.app.push_index_progress()
