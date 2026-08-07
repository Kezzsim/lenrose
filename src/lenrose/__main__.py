"""Lenrose command-line entry point.

The primary way to run Lenrose is the bare ``lenrose`` command, which:

1. Recovers any half-written state from a prior crash.
2. Runs the interactive setup TUI if the app has not been configured yet
   (or if ``--reconfigure`` is passed), then continues once setup completes.
3. Ensures the web frontend is built (building it on first run if needed).
4. Starts the FastAPI server, serving the search UI at ``/`` and the API at
   ``/api``.

The ``tui`` and ``serve`` subcommands remain available for development and for
running the components in isolation.
"""

from __future__ import annotations

import argparse
import logging
import sys

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8001


def _run_setup_tui() -> bool:
    from lenrose.tui.app import run as run_tui

    return run_tui()


def _start_server(host: str, port: int) -> None:
    from lenrose.server.app import run as run_server

    run_server(host=host, port=port)


def run_app(host: str, port: int, reconfigure: bool = False) -> int:
    """Unified launcher: setup-if-needed, build frontend, then serve."""
    from lenrose.server.frontend import ensure_frontend_built
    from lenrose.state import db

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("lenrose")

    db.init_db()
    db.reconcile_orphaned_state()

    if reconfigure or not db.is_setup_complete():
        if reconfigure:
            log.info("Launching setup TUI (--reconfigure).")
        else:
            log.info("No prior setup found; launching setup TUI.")
        completed = _run_setup_tui()
        if not completed:
            log.info("Setup was not completed; exiting without starting the server.")
            return 0
    else:
        log.info("Existing configuration found; starting the server.")

    ensure_frontend_built()

    log.info("Serving Lenrose on http://%s:%s (UI at /, API at /api).", host, port)
    _start_server(host, port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lenrose", description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server bind host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    parser.add_argument(
        "--reconfigure",
        action="store_true",
        help="Run the setup TUI even if the app is already configured",
    )

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("tui", help="Launch the interactive ingestion TUI only")
    serve = sub.add_parser("serve", help="Run the search web server only")
    serve.add_argument("--host", default=DEFAULT_HOST)
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)

    args = parser.parse_args(argv)

    if args.command == "tui":
        _run_setup_tui()
        return 0
    if args.command == "serve":
        _start_server(args.host, args.port)
        return 0

    # Default: unified launcher.
    return run_app(host=args.host, port=args.port, reconfigure=args.reconfigure)


if __name__ == "__main__":
    sys.exit(main())
