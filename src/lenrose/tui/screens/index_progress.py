"""Index progress screen: build the Typesense collection and ingest records."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Label, ProgressBar, Static

from lenrose.config import get_settings
from lenrose.indexer.rebuild import persisted_key_specs, rebuild
from lenrose.indexer.typesense_client import get_client
from lenrose.state import db


class IndexProgressScreen(Screen):
    """Persist state, build the schema and ingest all selected containers."""

    CSS = """
    Vertical { padding: 1 2; }
    #log { height: 1fr; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Building index")
            yield ProgressBar(total=100, id="bar")
            yield Static("", id="log")
            yield Button("Done", variant="primary", id="done", disabled=True)

    def on_mount(self) -> None:
        self.run_worker(self._build, thread=True)

    def _build(self) -> None:
        settings = get_settings()
        ctx = self.app.ctx
        log = self.query_one("#log", Static)
        bar = self.query_one("#bar", ProgressBar)

        # Recover from any half-written state left by a prior crash before we
        # start, so we never resume from selections that were never indexed.
        db.init_db()
        db.reconcile_orphaned_state()
        specs = persisted_key_specs(ctx.key_specs)

        def progress(done: int, total: int, message: str) -> None:
            pct = int(done / max(total, 1) * 100)
            self.app.call_from_thread(bar.update, progress=pct)
            self.app.call_from_thread(log.update, message)

        # Store & index first; only persist selections once a collection is
        # successfully stored and indexed. On any failure, wipe the state DB so
        # a partially-written run cannot cause duplicated objects on retry.
        try:
            ts_client = get_client(settings)
            count = rebuild(
                ts_client,
                ctx.client,
                settings.lenrose_index_name,
                ctx.selected_containers,
                specs,
                progress=progress,
            )
        except Exception as exc:
            db.reset_state_db()
            self.app.call_from_thread(log.update, f"Indexing failed (state wiped): {exc}")
            self.app.call_from_thread(
                self.query_one("#done", Button).__setattr__, "disabled", False
            )
            return

        # Rebuild succeeded and recorded an IndexState. Persist the selections
        # that produced this collection so the app can resume cleanly.
        try:
            db.save_containers(ctx.selected_containers)
            db.save_key_specs(specs)
        except Exception as exc:
            db.reset_state_db()
            self.app.call_from_thread(log.update, f"Failed to persist state (wiped): {exc}")
            self.app.call_from_thread(
                self.query_one("#done", Button).__setattr__, "disabled", False
            )
            return

        self.app.call_from_thread(bar.update, progress=100)
        self.app.call_from_thread(log.update, f"Indexed {count} records.")
        self.app.call_from_thread(
            self.query_one("#done", Button).__setattr__, "disabled", False
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "done":
            self.app.exit()
