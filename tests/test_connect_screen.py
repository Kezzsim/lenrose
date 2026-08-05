"""Tests for the Tiled connection screen helpers."""

from __future__ import annotations

from lenrose.tui.screens.connect import _port_from_uri, _uri_with_port


def test_uri_with_port_adds_port_to_tiled_uri():
    assert _uri_with_port("http://localhost", 8000) == "http://localhost:8000"


def test_uri_with_port_replaces_existing_port():
    assert _uri_with_port("https://tiled.example.com:443/api", 8000) == (
        "https://tiled.example.com:8000/api"
    )


def test_port_from_uri_extracts_existing_port():
    assert _port_from_uri("http://localhost:8000") == "8000"
