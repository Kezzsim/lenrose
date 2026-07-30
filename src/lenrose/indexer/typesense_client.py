"""Typesense native client factory."""

from __future__ import annotations

import typesense

from lenrose.config import get_settings


def get_client(settings=None) -> typesense.Client:
    settings = settings or get_settings()
    return typesense.Client(
        {
            "nodes": settings.typesense_nodes,
            "api_key": settings.typesense_api_key,
            "connection_timeout_seconds": 10,
        }
    )
