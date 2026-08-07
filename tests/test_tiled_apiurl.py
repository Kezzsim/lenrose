"""Tests for how the browser-facing Tiled API URL is resolved.

The web app loads record data directly from Tiled, so it must be pointed at the
same server the data was ingested from. The URL is resolved with this
precedence: env override (LENROSE_TILED_PUBLIC_URI / LENROSE_TILED_URI) first,
then the Tiled connection the user saved in the TUI (state DB).
"""

from __future__ import annotations

import pytest

from lenrose.server import tiled_session
from lenrose.state import db


@pytest.fixture
def temp_db(tmp_path):
    db.get_engine(str(tmp_path / "state.db"))
    db.init_db()
    yield
    db._engine = None


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("LENROSE_TILED_PUBLIC_URI", raising=False)
    monkeypatch.delenv("LENROSE_TILED_URI", raising=False)
    monkeypatch.delenv("TILED_API_KEY", raising=False)


def test_apiurl_from_saved_connection(temp_db, clean_env):
    db.save_connection(uri="https://tiled-demo.nsls2.bnl.gov", auth_method="anonymous")

    summary = tiled_session.server_tiled_summary()

    assert summary["apiUrl"] == "https://tiled-demo.nsls2.bnl.gov/api/v1"
    assert summary["configured"] is True
    assert summary["method"] == "anonymous"


def test_env_overrides_saved_connection(temp_db, clean_env, monkeypatch):
    db.save_connection(uri="https://tiled-demo.nsls2.bnl.gov", auth_method="anonymous")
    monkeypatch.setenv("LENROSE_TILED_URI", "http://localhost:8000")

    assert tiled_session._tiled_api_url() == "http://localhost:8000/api/v1"


def test_public_uri_wins_over_internal(temp_db, clean_env, monkeypatch):
    monkeypatch.setenv("LENROSE_TILED_URI", "http://internal:8000")
    monkeypatch.setenv("LENROSE_TILED_PUBLIC_URI", "https://public.example.com")

    assert tiled_session._tiled_api_url() == "https://public.example.com/api/v1"


def test_no_connection_no_env_is_unconfigured(temp_db, clean_env):
    summary = tiled_session.server_tiled_summary()

    assert summary["apiUrl"] is None
    assert summary["configured"] is False
    assert summary["method"] is None


def test_apiurl_not_double_suffixed(temp_db, clean_env):
    db.save_connection(uri="https://tiled-demo.nsls2.bnl.gov/api/v1")

    assert (
        tiled_session._tiled_api_url()
        == "https://tiled-demo.nsls2.bnl.gov/api/v1"
    )
