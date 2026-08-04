"""Rebuild a Typesense collection (index) from scratch.

Typesense collection schemas are not mutable in place, so schema changes
(including key expansion) go through a full drop-and-recreate here.
"""

from __future__ import annotations

from typesense.exceptions import ObjectNotFound

from lenrose.indexer.ingest import (
    documents_from_container,
    import_documents,
    normalize_collection,
)
from lenrose.schema.builder import build_schema, system_key_specs
from lenrose.state import db
from lenrose.state.models import KeySpec, SelectedContainer


def recreate_collection(ts_client, index_name: str, key_specs: list[KeySpec]) -> None:
    """Drop (if present) and create the collection with a fresh schema."""
    try:
        ts_client.collections[index_name].delete()
    except ObjectNotFound:
        pass  # collection may not exist yet
    schema = build_schema(index_name, key_specs)
    ts_client.collections.create(schema)


def rebuild(
    ts_client,
    tiled_client,
    index_name: str,
    containers: list[SelectedContainer],
    key_specs: list[KeySpec],
    progress=None,
) -> int:
    """Full rebuild: recreate schema, then ingest all selected containers.

    ``progress`` is an optional callable ``(done, total, message)``.
    Returns total number of documents indexed.
    """
    recreate_collection(ts_client, index_name, key_specs)

    total_indexed = 0
    active = [c for c in containers if c.selected]
    for idx, container in enumerate(active):
        collection = normalize_collection(container.path)
        node = tiled_client[container.path]
        docs = documents_from_container(
            node, collection, key_specs, limit=container.result_limit
        )
        total_indexed += import_documents(ts_client, index_name, docs)
        if progress is not None:
            progress(idx + 1, len(active), f"Indexed {container.path}")

    db.upsert_index_state(index_name, record_count=total_indexed)
    return total_indexed


def persisted_key_specs(user_specs: list[KeySpec]) -> list[KeySpec]:
    """Combine locked system specs with user-selected specs."""
    return system_key_specs() + [s for s in user_specs if not s.is_system]
