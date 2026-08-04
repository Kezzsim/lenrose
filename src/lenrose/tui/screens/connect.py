"""Connect screen: gather Tiled URI and authentication details."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Label, Select, Static

from lenrose.state import db
from lenrose.tiled_client.auth import AuthMethod, TiledConnectionInfo, connect


def _port_from_uri(uri: str) -> str:
    try:
        port = urlsplit(uri).port
    except ValueError:
        return ""
    return str(port) if port is not None else ""


def _uri_with_port(uri: str, port: int | None) -> str:
    if port is None:
        return uri

    parts = urlsplit(uri)
    if not parts.scheme or not parts.netloc:
        return uri

    hostname = parts.hostname
    if not hostname:
        return uri

    userinfo = ""
    if "@" in parts.netloc:
        userinfo = f"{parts.netloc.rsplit('@', 1)[0]}@"
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    netloc = f"{userinfo}{hostname}:{port}"
    return urlunsplit(parts._replace(netloc=netloc))


class ConnectScreen(Screen):
    """First screen: connect to a Tiled server."""

    CSS = """
    Vertical { padding: 1 2; }
    Input, Select { margin: 1 0; }
    #status { color: $error; }
    """

    def compose(self) -> ComposeResult:
        # Prefill from the last saved connection so a previous unexpected quit
        # does not force the user to re-enter server details.
        last = None
        try:
            last = db.load_last_connection()
        except Exception:
            last = None

        yield Header()
        with Vertical():
            yield Label("Connect to Tiled")
            yield Input(
                placeholder="https://tiled.example.com",
                value=last.uri if last else "",
                id="uri",
            )
            yield Input(
                placeholder="Tiled port, e.g. 8000",
                value=(_port_from_uri(last.uri) if last else ""),
                id="port",
            )
            yield Select(
                [(m.value, m.value) for m in AuthMethod],
                value=(last.auth_method if last else AuthMethod.ANONYMOUS.value),
                id="auth",
            )
            yield Input(
                placeholder="API key",
                value=(last.api_key if last and last.api_key else ""),
                id="api_key",
                password=True,
            )
            yield Input(
                placeholder="Username",
                value=(last.username if last and last.username else ""),
                id="username",
            )
            yield Input(
                placeholder="Password",
                value=(last.password if last and last.password else ""),
                id="password",
                password=True,
            )
            yield Button("Connect", variant="primary", id="connect")
            yield Static("", id="status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "connect":
            return
        status = self.query_one("#status", Static)
        uri = self.query_one("#uri", Input).value.strip()
        if not uri:
            status.update("Please enter a Tiled URI.")
            return
        port_value = self.query_one("#port", Input).value.strip()
        port = None
        if port_value:
            try:
                port = int(port_value)
            except ValueError:
                status.update("Tiled port must be a number.")
                return
            if port <= 0:
                status.update("Tiled port must be positive.")
                return
        uri = _uri_with_port(uri, port)
        method = AuthMethod(self.query_one("#auth", Select).value)
        info = TiledConnectionInfo(
            uri=uri,
            auth_method=method,
            api_key=self.query_one("#api_key", Input).value or None,
            username=self.query_one("#username", Input).value or None,
            password=self.query_one("#password", Input).value or None,
        )
        status.update("Connecting...")
        try:
            client = connect(info)
        except Exception as exc:  # surface any auth/connection error
            status.update(f"Connection failed: {exc}")
            return

        self.app.ctx.connection = info
        self.app.ctx.client = client

        # Persist details immediately so an unexpected quit later in the flow
        # does not lose them. Failure to save must not block the user.
        try:
            db.save_connection(
                uri=info.uri,
                auth_method=info.auth_method.value,
                username=info.username,
                api_key=info.api_key,
                password=info.password,
            )
        except Exception:
            pass

        self.app.push_container_select()
