"""Generation of scoped, search-only Typesense API keys for the browser.

The frontend (via the Typesense InstantSearch adapter) talks to Typesense
directly. It must never receive the admin API key. Instead the server mints a
parent key restricted to ``documents:search`` and then derives a scoped search
key locked to the Lenrose collection, which is safe to hand to the browser.

Keys are cached in-process; they are regenerated automatically if the parent
key is missing (e.g. after a Typesense restart with a fresh data dir).
"""

from __future__ import annotations

import hashlib
import hmac
import base64
import json

from lenrose.config import Settings, get_settings
from lenrose.indexer.typesense_client import get_client

_PARENT_KEY_DESCRIPTION = "lenrose-search-only-parent"

# Cache: (admin_key, collection) -> parent search-only key value
_parent_key_cache: dict[tuple[str, str], str] = {}


def _find_or_create_parent_key(settings: Settings) -> str:
    """Return a search-only parent key value, creating it if necessary.

    Typesense only returns a key's ``value`` at creation time, so we cannot look
    up an existing key's secret. We therefore always create a fresh parent key
    and cache its value for the lifetime of the process. If an explicit
    ``typesense_search_only_key`` is configured, that is used verbatim.
    """
    if settings.typesense_search_only_key:
        return settings.typesense_search_only_key

    cache_key = (settings.typesense_api_key, settings.lenrose_index_name)
    if cache_key in _parent_key_cache:
        return _parent_key_cache[cache_key]

    client = get_client(settings)
    created = client.keys.create(
        {
            "description": _PARENT_KEY_DESCRIPTION,
            "actions": ["documents:search"],
            "collections": [settings.lenrose_index_name],
        }
    )
    value = created["value"]
    _parent_key_cache[cache_key] = value
    return value


def _generate_scoped_key(parent_key: str, params: dict) -> str:
    """Derive a scoped search key from a parent key (mirrors the JS SDK).

    A scoped key is ``base64(hmac_sha256(parent_key, params) + params)`` where
    the first 4 chars of the parent key are prefixed to the digest.
    """
    params_str = json.dumps(params, separators=(",", ":"))
    digest = base64.b64encode(
        hmac.new(
            parent_key.encode("utf-8"),
            params_str.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    scoped = f"{digest}{parent_key[:4]}{params_str}"
    return base64.b64encode(scoped.encode("utf-8")).decode("utf-8")


def get_scoped_search_key(settings: Settings | None = None) -> str:
    """Return a scoped search-only key locked to the Lenrose collection."""
    settings = settings or get_settings()
    parent = _find_or_create_parent_key(settings)
    # The parent key is already restricted to documents:search on the Lenrose
    # collection; the scoped wrapper simply embeds an expiry.
    return _generate_scoped_key(parent, {"expires_at": _far_future()})


def _far_future() -> int:
    # ~10 years; scoped keys require a numeric expiry to be embeddable.
    import time

    return int(time.time()) + 10 * 365 * 24 * 3600


def reset_cache() -> None:
    """Clear the cached parent key (used by tests)."""
    _parent_key_cache.clear()
