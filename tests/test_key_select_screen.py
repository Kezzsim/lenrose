"""Regression tests for the KeySelectScreen.

Dotted metadata keys flattened from Tiled (e.g. ``start.plan_name``) once
crashed this screen because they were used verbatim as Textual widget IDs,
which permit only letters, numbers, underscores and hyphens. These tests drive
the real screen to guarantee nested keys mount and build valid specs.
"""

from __future__ import annotations

import pytest
from textual.app import App
from textual.widgets import Checkbox, RadioButton

from lenrose.state.models import SelectedContainer
from lenrose.tui.context import IngestContext
from lenrose.tui.screens.key_select import KeySelectScreen


class _Harness(App):
    def __init__(self, client) -> None:
        super().__init__()
        self.ctx = IngestContext()
        self.ctx.client = client
        self.ctx.selected_containers = [
            SelectedContainer(path="", result_limit=100)
        ]
        self.index_progress_pushed = False

    def push_index_progress(self) -> None:
        self.index_progress_pushed = True


@pytest.mark.asyncio
async def test_dotted_keys_mount_without_crash(fake_container):
    """All flattened dotted keys must mount as widgets (no BadIdentifier)."""
    app = _Harness(fake_container)
    async with app.run_test() as pilot:
        await app.push_screen(KeySelectScreen())
        await pilot.pause()
        screen = app.screen
        incs = [w for w in screen.query(Checkbox) if str(w.id).startswith("inc-")]
        # start.plan_name, start.num_points, start.detectors, sample.name ...
        assert len(incs) >= 4
        # Every discovered key is a dotted, flattened path.
        assert all("." in k for k in screen._discovered)
        # Widget IDs never contain the illegal dot character.
        assert all("." not in str(w.id) for w in incs)


@pytest.mark.asyncio
async def test_build_produces_specs_for_nested_keys(fake_container):
    """Building must yield KeySpecs that preserve the true dotted keys."""
    app = _Harness(fake_container)
    async with app.run_test() as pilot:
        await app.push_screen(KeySelectScreen())
        await pilot.pause()
        screen = app.screen

        # Keep only one nested key selected and facet it.
        incs = [w for w in screen.query(Checkbox) if str(w.id).startswith("inc-")]
        for w in incs[1:]:
            w.value = False
        facs = [w for w in screen.query(Checkbox) if str(w.id).startswith("fac-")]
        facs[0].value = True

        screen.query_one("#build").press()
        await pilot.pause()

        assert app.index_progress_pushed
        assert len(app.ctx.key_specs) == 1
        spec = app.ctx.key_specs[0]
        assert "." in spec.dotted_key
        assert spec.is_facet is True
        assert spec.parent == spec.dotted_key.rsplit(".", 1)[0]


@pytest.mark.asyncio
async def test_bulk_key_selection_buttons(fake_container):
    """Bulk controls must select and deselect include and facet checkboxes."""
    app = _Harness(fake_container)
    async with app.run_test() as pilot:
        await app.push_screen(KeySelectScreen())
        await pilot.pause()
        screen = app.screen

        incs = [w for w in screen.query(Checkbox) if str(w.id).startswith("inc-")]
        facs = [w for w in screen.query(Checkbox) if str(w.id).startswith("fac-")]
        assert incs
        assert facs

        screen.query_one("#deselect-all-included").press()
        await pilot.pause()
        assert all(not w.value for w in incs)

        screen.query_one("#select-all-included").press()
        await pilot.pause()
        assert all(w.value for w in incs)

        screen.query_one("#select-all-faceted").press()
        await pilot.pause()
        assert all(w.value for w in facs)

        screen.query_one("#deselect-all-faceted").press()
        await pilot.pause()
        assert all(not w.value for w in facs)


@pytest.mark.asyncio
async def test_display_selector_mounts_for_all_keys(fake_container):
    """Any discovered metadata key may be selected as the display label."""
    app = _Harness(fake_container)
    async with app.run_test() as pilot:
        await app.push_screen(KeySelectScreen())
        await pilot.pause()
        screen = app.screen

        display_keys = {screen._slots[slot] for slot in screen._display_slots}
        assert display_keys == set(screen._discovered)
        assert "start.plan_name" in display_keys
        assert len(list(screen.query(RadioButton))) == len(screen._discovered)


@pytest.mark.asyncio
async def test_display_selector_marks_name_spec(fake_container):
    """Selecting a name display option persists it on the built KeySpec."""
    app = _Harness(fake_container)
    async with app.run_test() as pilot:
        await app.push_screen(KeySelectScreen())
        await pilot.pause()
        screen = app.screen
        slot = next(slot for slot, key in screen._slots.items() if key == "sample.name")

        screen.query_one(f"#disp-{slot}", RadioButton).value = True
        screen.query_one(f"#inc-{slot}", Checkbox).value = False
        screen.query_one("#build").press()
        await pilot.pause()

        display_specs = [spec for spec in app.ctx.key_specs if spec.is_display]
        assert len(display_specs) == 1
        assert display_specs[0].dotted_key == "sample.name"
        assert display_specs[0].is_facet is False


@pytest.mark.asyncio
async def test_display_selector_clears_facet_checkbox(fake_container):
    """Selecting a display name must stop that field appearing as a facet."""
    app = _Harness(fake_container)
    async with app.run_test() as pilot:
        await app.push_screen(KeySelectScreen())
        await pilot.pause()
        screen = app.screen
        slot = next(slot for slot, key in screen._slots.items() if key == "sample.name")

        screen.query_one(f"#fac-{slot}", Checkbox).value = True
        screen.query_one(f"#disp-{slot}", RadioButton).value = True
        await pilot.pause()
        screen.query_one("#build").press()
        await pilot.pause()

        assert screen.query_one(f"#fac-{slot}", Checkbox).value is False
        display_spec = next(spec for spec in app.ctx.key_specs if spec.is_display)
        assert display_spec.dotted_key == "sample.name"
        assert display_spec.is_facet is False


@pytest.mark.asyncio
async def test_display_selector_allows_only_one_name_field(fake_container):
    """Radio-style display selectors must be mutually exclusive."""
    container_cls = type(fake_container)
    node_cls = type(next(iter(fake_container.children.values())))
    container = container_cls(
        children={
            "scan_001": node_cls(
                metadata={
                    "sample": {"name": "Fe2O3"},
                    "instrument": {"name": "TES"},
                }
            )
        }
    )
    app = _Harness(container)
    async with app.run_test() as pilot:
        await app.push_screen(KeySelectScreen())
        await pilot.pause()
        screen = app.screen
        slots = sorted(screen._display_slots)
        assert len(slots) == 2

        screen.query_one(f"#disp-{slots[0]}", RadioButton).value = True
        await pilot.pause()
        screen.query_one(f"#disp-{slots[1]}", RadioButton).value = True
        await pilot.pause()

        assert screen.query_one(f"#disp-{slots[0]}", RadioButton).value is False
        assert screen.query_one(f"#disp-{slots[1]}", RadioButton).value is True
