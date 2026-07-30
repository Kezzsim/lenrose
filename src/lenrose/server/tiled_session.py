"""Server-side Tiled client session.

The web server needs a Tiled client to load full records on demand and to
ingest records referenced by webhooks. It is configured from the environment
via ``LENROSE_TILED_URI`` (and optional ``TILED_API_KEY``).
"""

from __future__ import annotations

import os

from lenrose.tiled_client.auth import AuthMethod, TiledConnectionInfo, connect

_client = None
_resolved = False


def get_tiled_client():
    """Return a cached server-side Tiled client, or None if not configured."""
    global _client, _resolved
    if _resolved:
        return _client
    _resolved = True

    uri = os.environ.get("LENROSE_TILED_URI")
    if not uri:
        _client = None
        return None

    api_key = os.environ.get("TILED_API_KEY")
    info = TiledConnectionInfo(
        uri=uri,
        auth_method=AuthMethod.API_KEY if api_key else AuthMethod.ANONYMOUS,
        api_key=api_key,
    )
    try:
        _client = connect(info)
    except Exception:
        _client = None
    return _client


def reset_tiled_client() -> None:
    global _client, _resolved
    _client = None
    _resolved = False
