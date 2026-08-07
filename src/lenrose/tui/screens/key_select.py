"""Key selection screen: discovered keys with facet/index/searchable toggles."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Header, Label, RadioButton, Static

from lenrose.schema.inference import parent_of
from lenrose.state.models import KeySpec
from lenrose.tiled_client.introspect import introspect_container


class KeySelectScreen(Screen):
    """Choose which metadata keys to index and their facet/index options."""

    CSS = """
    VerticalScroll { padding: 1 2; height: 1fr; min-height: 15; }
    .row { height: auto; }
    .keyname { width: 1fr; min-width: 30; }
    .display { width: 18; }
    #status { color: $warning; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Select metadata keys to index (include / facet)")
            yield Static("collection is always indexed and faceted by default.")
            with Horizontal():
                yield Button("Select all included", id="select-all-included")
                yield Button("Deselect all included", id="deselect-all-included")
                yield Button("Select all facets", id="select-all-faceted")
                yield Button("Deselect all facets", id="deselect-all-faceted")
            yield VerticalScroll(id="keys")
            yield Static("", id="status")
            with Horizontal():
                yield Button("Build index", variant="success", id="build")

    def on_mount(self) -> None:
        self._slots: dict[int, str] = {}
        self._display_slots: set[int] = set()
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
        header = Horizontal(classes="row")
        listing.mount(header)
        header.mount(Static("include / key", classes="keyname"))
        header.mount(Static("facet"))
        header.mount(Static("display", classes="display"))
        # Textual widget IDs may contain only letters, numbers, underscores and
        # hyphens, so the dotted keys coming from Tiled (e.g.
        # ``start.BMM_motors.m1_pitch``) cannot be used directly. Assign each
        # key a stable positional slot and key the widgets off that slot,
        # keeping the real dotted key in ``self._slots`` for building specs.
        for slot, (dotted, dtype) in enumerate(sorted(merged.items())):
            self._slots[slot] = dotted
            row = Horizontal(classes="row")
            listing.mount(row)
            row.mount(
                Checkbox(f"{dotted} [{dtype}]", value=True,
                         id=f"inc-{slot}", classes="keyname")
            )
            row.mount(Checkbox("facet", value=False, id=f"fac-{slot}"))
            self._display_slots.add(slot)
            row.mount(RadioButton("name", value=False, id=f"disp-{slot}", classes="display"))
        self._discovered = merged

    def on_radio_button_changed(self, event: RadioButton.Changed) -> None:
        if not event.radio_button.id or not event.radio_button.id.startswith("disp-"):
            return
        if not event.value:
            return
        selected_slot = int(event.radio_button.id.removeprefix("disp-"))
        self.query_one(f"#fac-{selected_slot}", Checkbox).value = False
        for slot in self._display_slots:
            if slot == selected_slot:
                continue
            self.query_one(f"#disp-{slot}", RadioButton).value = False
        self.query_one(f"#inc-{selected_slot}", Checkbox).value = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select-all-included":
            self._set_key_checkboxes("inc", True)
            return
        if event.button.id == "deselect-all-included":
            self._set_key_checkboxes("inc", False)
            return
        if event.button.id == "select-all-faceted":
            self._set_key_checkboxes("fac", True)
            return
        if event.button.id == "deselect-all-faceted":
            self._set_key_checkboxes("fac", False)
            return
        if event.button.id != "build":
            return
        specs: list[KeySpec] = []
        for slot, dotted in self._slots.items():
            dtype = self._discovered[dotted]
            inc = self.query_one(f"#inc-{slot}", Checkbox).value
            display = (
                slot in self._display_slots
                and self.query_one(f"#disp-{slot}", RadioButton).value
            )
            if display:
                inc = True
            if not inc:
                continue
            fac = self.query_one(f"#fac-{slot}", Checkbox).value and not display
            specs.append(
                KeySpec(
                    dotted_key=dotted,
                    parent=parent_of(dotted),
                    datatype=dtype,
                    is_facet=fac,
                    is_index=True,
                    is_searchable=dtype.startswith("string"),
                    is_display=display,
                    is_system=False,
                    selected=True,
                )
            )
        self.app.ctx.key_specs = specs
        self.app.push_index_progress()

    def _set_key_checkboxes(self, prefix: str, value: bool) -> None:
        for slot in self._slots:
            self.query_one(f"#{prefix}-{slot}", Checkbox).value = value
        if prefix == "inc" and not value:
            for slot in self._display_slots:
                self.query_one(f"#disp-{slot}", RadioButton).value = False
