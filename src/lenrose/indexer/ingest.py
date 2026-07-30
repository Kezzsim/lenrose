"""Ingest Tiled metadata into a Typesense collection."""

from __future__ import annotations

from typing import Iterable

from lenrose.schema.inference import (
    SYSTEM_FIELD_NAMES,
    sanitize_field_name,
)
from lenrose.state.models import KeySpec
from lenrose.tiled_client.introspect import flatten


def normalize_collection(collection: str) -> str:
    """Canonicalise a container path into a single stable collection string.

    A Tiled object must map to exactly one Typesense document ``id`` regardless
    of whether it was ingested via the batch/TUI path (``SelectedContainer.path``)
    or the webhook path (``"/".join(payload["path"])``). Without this,
    ``"pokemon"``, ``"pokemon/"``, ``"/pokemon"`` and ``["pokemon"]`` produce
    distinct ``id`` prefixes for the same record, duplicating it.

    Rules: strip surrounding whitespace, collapse repeated slashes, and strip
    leading/trailing slashes. The empty string denotes the root container.
    """
    if collection is None:
        return ""
    segments = [seg for seg in str(collection).strip().split("/") if seg]
    return "/".join(segments)


def make_doc_id(collection: str, uuid: str) -> str:
    """Stable Typesense document id / tiled_key for a record.

    Uses the normalized collection so the same underlying Tiled object always
    resolves to one id. For the root container (empty collection) the id is
    just the uuid, avoiding a spurious leading slash.
    """
    collection = normalize_collection(collection)
    return f"{collection}/{uuid}" if collection else str(uuid)


def build_document(
    uuid: str,
    collection: str,
    metadata: dict,
    selected_keys: set[str],
    structure_family: str | None = None,
    specs: list[str] | None = None,
) -> dict:
    """Build a single Typesense document from a record's metadata.

    Always includes system fields ``uuid``, ``collection`` and ``tiled_key``.
    ``collection`` is normalized so a Tiled object maps to exactly one document
    ``id``. ``tiled_key`` equals ``id`` and is used to reload the full record
    from Tiled, e.g. ``client["pokemon/{uuid}"]``.
    """
    collection = normalize_collection(collection)
    doc_id = make_doc_id(collection, uuid)
    doc: dict = {
        "id": doc_id,
        "uuid": uuid,
        "collection": collection,
        "tiled_key": doc_id,
    }
    if structure_family is not None:
        doc["structure_family"] = structure_family
    if specs is not None:
        doc["specs"] = list(specs)

    flat = flatten(dict(metadata or {}))
    for dotted, value in flat.items():
        if dotted not in selected_keys:
            continue
        field_name = sanitize_field_name(dotted)
        if field_name in SYSTEM_FIELD_NAMES:
            continue
        doc[field_name] = value
    return doc


def documents_from_container(
    container_client,
    collection: str,
    key_specs: Iterable[KeySpec],
    limit: int = 100,
) -> list[dict]:
    """Produce Typesense documents for every record in a container."""
    selected_keys = {
        s.dotted_key for s in key_specs if s.selected and not s.is_system
    }
    docs: list[dict] = []
    for key, node in container_client.items()[:limit]:
        uuid = str(key)
        metadata = dict(node.metadata or {})
        structure_family = _as_str(getattr(node, "structure_family", None))
        specs = _specs_as_list(getattr(node, "specs", None))
        docs.append(
            build_document(
                uuid=uuid,
                collection=collection,
                metadata=metadata,
                selected_keys=selected_keys,
                structure_family=structure_family,
                specs=specs,
            )
        )
    return docs


def import_documents(ts_client, index_name: str, documents: list[dict]) -> int:
    """Upsert documents into Typesense. Returns count imported."""
    if not documents:
        return 0
    ts_client.collections[index_name].documents.import_(
        documents, {"action": "upsert"}
    )
    return len(documents)


def _as_str(value) -> str | None:
    if value is None:
        return None
    return str(value)


def _specs_as_list(specs) -> list[str] | None:
    if not specs:
        return None
    out: list[str] = []
    for s in specs:
        name = getattr(s, "name", s)
        out.append(str(name))
    return out
