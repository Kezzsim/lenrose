"""Tiled client construction and authentication helpers.

Follows the Tiled "Custom Applications" guidance so we avoid the CLI prompt
helpers and can drive auth from a TUI. See:
https://blueskyproject.io/tiled/user-guide/authentication.html
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuthMethod(str, Enum):
    ANONYMOUS = "anonymous"
    API_KEY = "api_key"
    PASSWORD = "password"


@dataclass
class TiledConnectionInfo:
    uri: str
    auth_method: AuthMethod = AuthMethod.ANONYMOUS
    api_key: str | None = None
    username: str | None = None
    password: str | None = None


def connect(info: TiledConnectionInfo):
    """Construct a Tiled client from connection info.

    Returns the root container client. Raises on failure so callers (TUI) can
    surface the error interactively.
    """
    from tiled.client import from_uri

    if info.auth_method == AuthMethod.API_KEY:
        if not info.api_key:
            raise ValueError("API key auth selected but no api_key provided")
        return from_uri(info.uri, api_key=info.api_key)

    if info.auth_method == AuthMethod.PASSWORD:
        return _connect_password(info)

    # Anonymous
    return from_uri(info.uri)


def _connect_password(info: TiledConnectionInfo):
    """Password grant flow driven programmatically (no interactive prompt)."""
    from tiled.client import from_context
    from tiled.client.context import Context

    if not info.username or not info.password:
        raise ValueError("Password auth requires username and password")

    context, node_path_parts = Context.from_any_uri(info.uri)
    # Context.authenticate performs the OAuth2 password grant when the server
    # is configured for it; provide credentials directly.
    context.authenticate(username=info.username, password=info.password)
    return from_context(context, node_path_parts=node_path_parts)
