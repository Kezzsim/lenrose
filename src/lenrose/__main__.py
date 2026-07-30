"""Lenrose command-line entry point."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lenrose", description=__doc__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("tui", help="Launch the interactive ingestion TUI")
    serve = sub.add_parser("serve", help="Run the search web server")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "tui":
        from lenrose.tui.app import run as run_tui

        run_tui()
        return 0
    if args.command == "serve":
        from lenrose.server.app import run as run_server

        run_server(host=args.host, port=args.port)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
