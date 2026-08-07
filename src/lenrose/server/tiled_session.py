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


def server_tiled_summary() -> dict:
    """Describe the server's preconfigured Tiled connection (no secrets).

    Used by the frontend to label the default ("preconfigured") auth option and
    to decide whether a preconfigured connection is even available.
    """
    uri = os.environ.get("LENROSE_TILED_URI")
    if not uri:
        return {"configured": False, "method": None}
    method = (
        AuthMethod.API_KEY.value
        if os.environ.get("TILED_API_KEY")
        else AuthMethod.ANONYMOUS.value
    )
    return {"configured": True, "method": method}


def client_from_credentials(
    method: str | None,
    api_key: str | None = None,
    username: str | None = None,
    password: str | None = None,
):
    """Build a Tiled client from caller-supplied credentials.

    Mirrors the TUI auth options (anonymous, API key, username/password). Falls
    back to the server-side client when no method is supplied. Returns None if
    Tiled is not configured or the connection fails.
    """
    if not method:
        return get_tiled_client()

    uri = os.environ.get("LENROSE_TILED_URI")
    if not uri:
        return None

    try:
        method_enum = AuthMethod(method)
    except ValueError:
        return None

    info = TiledConnectionInfo(
        uri=uri,
        auth_method=method_enum,
        api_key=api_key,
        username=username,
        password=password,
    )
    try:
        return connect(info)
    except Exception:
        return None
