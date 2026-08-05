"""Tests for the Typesense configuration TUI screen."""

from __future__ import annotations

import pytest
from textual.app import App
from textual.widgets import Input, Static

from lenrose.tui.context import IngestContext
from lenrose.tui.screens.typesense_config import TypesenseConfigScreen


class _Harness(App):
    def __init__(self) -> None:
        super().__init__()
        self.ctx = IngestContext()
        self.tiled_connect_pushed = False

    def push_tiled_connect(self) -> None:
        self.tiled_connect_pushed = True


@pytest.mark.asyncio
async def test_typesense_config_updates_context_settings():
    app = _Harness()
    async with app.run_test() as pilot:
        await app.push_screen(TypesenseConfigScreen())
        await pilot.pause()
        screen = app.screen

        screen.query_one("#host", Input).value = "typesense.example.com"
        screen.query_one("#port", Input).value = "443"
        screen.query_one("#protocol").value = "https"
        screen.query_one("#api_key", Input).value = "secret-key"

        screen.query_one("#continue").press()
        await pilot.pause()

        assert app.tiled_connect_pushed
        assert app.ctx.settings.typesense_host == "typesense.example.com"
        assert app.ctx.settings.typesense_port == 443
        assert app.ctx.settings.typesense_protocol == "https"
        assert app.ctx.settings.typesense_api_key == "secret-key"


@pytest.mark.asyncio
async def test_typesense_config_requires_numeric_port():
    app = _Harness()
    async with app.run_test() as pilot:
        await app.push_screen(TypesenseConfigScreen())
        await pilot.pause()
        screen = app.screen

        screen.query_one("#port", Input).value = "not-a-number"
        screen.query_one("#continue").press()
        await pilot.pause()

        assert not app.tiled_connect_pushed
        assert screen.query_one("#status", Static).content == "Typesense port must be a number."
