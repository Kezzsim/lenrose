"""Tests for SQLite state recovery after an improper shutdown.

The application persists what the user chose to index. If it crashes before a
Typesense collection is successfully stored and indexed, the leftover selections
are "orphaned" and must be wiped so the same Tiled objects are not indexed twice
on the next run.
"""

from __future__ import annotations

import pytest

from lenrose.state import db
from lenrose.state.models import KeySpec, SelectedContainer


@pytest.fixture
def temp_db(tmp_path):
    db.get_engine(str(tmp_path / "state.db"))
    db.init_db()
    yield
    db._engine = None  # reset cached engine for the next test


def test_orphaned_selections_without_index_are_detected_and_wiped(temp_db):
    db.save_containers([SelectedContainer(path="pokemon")])
    db.save_key_specs([KeySpec(dotted_key="start.plan_name")])

    assert db.has_orphaned_state() is True
    assert db.reconcile_orphaned_state() is True

    assert db.load_containers() == []
    assert db.load_key_specs() == []


def test_successful_index_is_not_treated_as_orphaned(temp_db):
    db.save_containers([SelectedContainer(path="pokemon")])
    db.save_key_specs([KeySpec(dotted_key="start.plan_name")])
    db.upsert_index_state("lenrose_records", record_count=60)

    assert db.has_orphaned_state() is False
    assert db.reconcile_orphaned_state() is False

    assert [c.path for c in db.load_containers()] == ["pokemon"]


def test_empty_db_is_not_orphaned(temp_db):
    assert db.has_orphaned_state() is False


def test_reset_state_db_clears_everything(temp_db):
    db.save_containers([SelectedContainer(path="pokemon")])
    db.upsert_index_state("lenrose_records", record_count=60)

    db.reset_state_db()

    assert db.load_containers() == []
    assert db.get_index_state("lenrose_records") is None


def test_connection_is_saved_and_restored(temp_db):
    assert db.load_last_connection() is None

    db.save_connection(
        uri="http://localhost:8000",
        auth_method="api_key",
        api_key="secret",
    )

    c = db.load_last_connection()
    assert c is not None
    assert c.uri == "http://localhost:8000"
    assert c.auth_method == "api_key"
    assert c.api_key == "secret"


def test_only_latest_connection_is_kept(temp_db):
    db.save_connection(uri="http://old:8000", auth_method="anonymous")
    db.save_connection(uri="http://new:8000", auth_method="anonymous")

    c = db.load_last_connection()
    assert c.uri == "http://new:8000"


def test_connection_survives_state_reset(temp_db):
    """A recovery wipe must not force the user to re-enter server details."""
    db.save_connection(uri="http://localhost:8000", auth_method="api_key", api_key="secret")
    db.save_containers([SelectedContainer(path="pokemon")])

    db.reset_state_db()

    assert db.load_containers() == []
    c = db.load_last_connection()
    assert c is not None
    assert c.uri == "http://localhost:8000"
