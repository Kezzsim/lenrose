#!/usr/bin/env python
"""Empty the backing service contents for a clean local development slate.

This wipes runtime *data* without tearing down containers or rotating
credentials:

* **Typesense** — deletes every collection via the native client, honouring the
  same host/port/protocol/API-key settings the application uses (so keys stay
  consistent across the stack).
* **Tiled** — resets the catalog by recreating the ``tiled`` container's data
  volume, then restarts the service so it reinitialises from empty.

Run it with ``pixi run services-empty`` (which ensures the stack is up first).
"""

from __future__ import annotations

import subprocess
import sys

from lenrose.config import get_settings


def _empty_typesense() -> None:
    settings = get_settings()
    try:
        from lenrose.indexer.typesense_client import get_client
    except Exception as exc:  # pragma: no cover - import guard
        print(f"[typesense] client unavailable, skipping: {exc}")
        return

    client = get_client(settings)
    try:
        collections = client.collections.retrieve()
    except Exception as exc:
        print(f"[typesense] could not reach server, skipping: {exc}")
        return

    if not collections:
        print("[typesense] already empty")
        return

    for collection in collections:
        name = collection["name"]
        client.collections[name].delete()
        print(f"[typesense] deleted collection {name!r}")


def _tiled_volume_name() -> str:
    """Resolve the Compose-qualified name of the tiled data volume.

    Compose prefixes volumes with the project name (the repo directory name by
    default, overridable via COMPOSE_PROJECT_NAME), so derive it rather than
    hard-coding the prefix.
    """
    result = subprocess.run(
        ["docker", "compose", "config", "--volumes"],
        capture_output=True,
        text=True,
    )
    # ``config --volumes`` lists the short names; combine with the project name.
    proj = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        capture_output=True,
        text=True,
    )
    import json
    import os

    project = os.environ.get("COMPOSE_PROJECT_NAME")
    if not project:
        try:
            project = json.loads(proj.stdout).get("name")
        except Exception:
            project = None
    project = project or os.path.basename(os.getcwd())
    short = "tiled-data"
    if "tiled-data" not in result.stdout.split():
        # Fall back to the known short name regardless.
        short = "tiled-data"
    return f"{project}_{short}"


def _empty_tiled() -> None:
    """Recreate the Tiled data volume so its catalog/storage start empty."""
    compose = ["docker", "compose"]
    volume = _tiled_volume_name()
    steps = [
        (compose + ["rm", "-sfv", "tiled"], "remove tiled container"),
        (["docker", "volume", "rm", "-f", volume],
         "remove tiled data volume"),
        (compose + ["up", "-d", "--wait", "tiled"], "recreate tiled"),
    ]
    for cmd, label in steps:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Volume removal can legitimately fail if it doesn't exist yet.
            print(f"[tiled] {label}: {result.stderr.strip() or 'skipped'}")
        else:
            print(f"[tiled] {label}: ok")


def main() -> int:
    print("Emptying service contents (containers and API keys preserved)...")
    _empty_typesense()
    _empty_tiled()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
