"""Tests for scoped search-only Typesense key generation."""

import base64

from lenrose.config import Settings
from lenrose.indexer import search_key


class _FakeKeys:
    def __init__(self):
        self.created = []

    def create(self, spec):
        self.created.append(spec)
        return {"value": "parent-secret-value", **spec}


class _FakeClient:
    def __init__(self):
        self.keys = _FakeKeys()


def test_generate_scoped_key_is_base64_and_embeds_params():
    scoped = search_key._generate_scoped_key(
        "parent-secret-value", {"expires_at": 9999999999}
    )
    decoded = base64.b64decode(scoped).decode("utf-8")
    # The parent-key prefix and the params JSON are embedded verbatim.
    assert "pare" in decoded  # first 4 chars of the parent key
    assert '"expires_at":9999999999' in decoded


def test_explicit_search_only_key_used_verbatim():
    settings = Settings(typesense_search_only_key="explicit-key")
    parent = search_key._find_or_create_parent_key(settings)
    assert parent == "explicit-key"


def test_parent_key_created_and_cached(monkeypatch):
    search_key.reset_cache()
    fake = _FakeClient()
    monkeypatch.setattr(search_key, "get_client", lambda settings: fake)

    settings = Settings(typesense_api_key="admin", lenrose_index_name="idx")
    first = search_key._find_or_create_parent_key(settings)
    second = search_key._find_or_create_parent_key(settings)

    assert first == "parent-secret-value"
    assert second == first
    # Created exactly once (cached thereafter) with a search-only action.
    assert len(fake.keys.created) == 1
    assert fake.keys.created[0]["actions"] == ["documents:search"]
    assert fake.keys.created[0]["collections"] == ["idx"]


def test_get_scoped_search_key_end_to_end(monkeypatch):
    search_key.reset_cache()
    fake = _FakeClient()
    monkeypatch.setattr(search_key, "get_client", lambda settings: fake)

    settings = Settings(typesense_api_key="admin", lenrose_index_name="idx")
    scoped = search_key.get_scoped_search_key(settings)
    # A non-empty base64 string that decodes cleanly.
    assert scoped
    base64.b64decode(scoped)
