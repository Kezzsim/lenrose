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


def _connection_uri() -> str | None:
    """URI of the most recent Tiled connection saved via the TUI, if any."""
    try:
        from lenrose.state import db

        connection = db.load_last_connection()
    except Exception:
        return None
    return connection.uri if connection else None


def _tiled_api_url() -> str | None:
    """Public Tiled API base URL for direct browser access.

    Source precedence (highest first):
      1. ``LENROSE_TILED_PUBLIC_URI`` / ``LENROSE_TILED_URI`` env — an explicit,
         browser-facing override that always wins.
      2. The Tiled connection the user saved in the TUI (state DB), so the web
         app talks to the same server the data was ingested from (e.g. a remote
         instance like tiled-demo) rather than a local Tiled.

    Returns the ``/api/v1`` REST base, never a secret.
    """
    uri = (
        os.environ.get("LENROSE_TILED_PUBLIC_URI")
        or os.environ.get("LENROSE_TILED_URI")
        or _connection_uri()
    )
    if not uri:
        return None
    base = uri.rstrip("/")
    if base.endswith("/api/v1"):
        return base
    return f"{base}/api/v1"


def server_tiled_summary() -> dict:
    """Describe the Tiled connection the browser should use (no secrets).

    Reports the public Tiled API URL for direct browser->Tiled data access,
    derived from the env override or the TUI-saved connection. Used by the
    frontend to decide whether direct Tiled access is possible and to label the
    auth options. Secrets (API keys) are never included.
    """
    api_url = _tiled_api_url()
    if api_url is None:
        return {"configured": False, "method": None, "apiUrl": None}

    # Prefer the saved connection's auth method when available; fall back to the
    # env-based method. This is a display hint only.
    method = None
    try:
        from lenrose.state import db

        connection = db.load_last_connection()
        if connection:
            method = connection.auth_method
    except Exception:
        method = None
    if method is None:
        method = (
            AuthMethod.API_KEY.value
            if os.environ.get("TILED_API_KEY")
            else AuthMethod.ANONYMOUS.value
        )

    return {"configured": True, "method": method, "apiUrl": api_url}


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
