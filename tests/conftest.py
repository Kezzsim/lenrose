"""Composable pytest fixtures for Lenrose tests.

Provides a Typesense connection fixture (points at the CI service container or
a locally running Typesense) and lightweight fakes for Tiled nodes so unit
tests can run without a live Tiled server. pytest-vcr is available for tests
that exercise real HTTP against Tiled.
"""

from __future__ import annotations

import os
import uuid as uuidlib
from dataclasses import dataclass, field

import pytest


# --- Typesense -------------------------------------------------------------

def _typesense_available() -> bool:
    try:
        import typesense  # noqa: F401
    except Exception:
        return False
    return True


@pytest.fixture
def vcr_config():
    return {
        "filter_headers": ["authorization", "x-tiled-signature"],
        "record_mode": "none",
    }


@pytest.fixture
def typesense_settings():
    from lenrose.config import Settings

    return Settings(
        typesense_host=os.environ.get("TYPESENSE_HOST", "localhost"),
        typesense_port=int(os.environ.get("TYPESENSE_PORT", "8108")),
        typesense_protocol=os.environ.get("TYPESENSE_PROTOCOL", "http"),
        typesense_api_key=os.environ.get("TYPESENSE_API_KEY", "secret"),
        lenrose_index_name=f"test_{uuidlib.uuid4().hex[:8]}",
    )


@pytest.fixture
def typesense_client(typesense_settings):
    if not _typesense_available():
        pytest.skip("typesense package not installed")
    from lenrose.indexer.typesense_client import get_client

    client = get_client(typesense_settings)
    try:
        client.collections.retrieve()
    except Exception:
        pytest.skip("Typesense server not reachable")
    yield client
    # cleanup
    try:
        client.collections[typesense_settings.lenrose_index_name].delete()
    except Exception:
        pass


# --- Fake Tiled nodes ------------------------------------------------------

@dataclass
class FakeNode:
    metadata: dict
    structure_family: str = "container"
    specs: list = field(default_factory=list)


@dataclass
class FakeContainer:
    """Minimal stand-in for a Tiled container client."""

    children: dict

    def keys(self):
        return list(self.children.keys())

    def __getitem__(self, key):
        # support "collection/uuid" style lookups one level deep
        if key in self.children:
            return self.children[key]
        raise KeyError(key)

    def __len__(self):
        return len(self.children)

    def items(self):
        return _ItemsView(self.children)


class _ItemsView:
    def __init__(self, children):
        self._children = children

    def __getitem__(self, sl):
        pairs = list(self._children.items())
        return pairs[sl]

    def __iter__(self):
        return iter(self._children.items())


@pytest.fixture
def fake_records():
    return {
        "scan_001": FakeNode(
            metadata={
                "start": {"plan_name": "count", "num_points": 5, "detectors": ["det1"]},
                "sample": {"name": "Fe2O3"},
            },
            structure_family="array",
            specs=["BlueskyRun"],
        ),
        "scan_002": FakeNode(
            metadata={
                "start": {"plan_name": "scan", "num_points": 10, "detectors": ["det1", "det2"]},
                "sample": {"name": "TiO2"},
            },
            structure_family="table",
            specs=[],
        ),
    }


@pytest.fixture
def fake_container(fake_records):
    return FakeContainer(children=fake_records)
