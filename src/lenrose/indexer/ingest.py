"""Ingest Tiled metadata into a Typesense collection."""

from __future__ import annotations

import json
from typing import Iterable

from lenrose.schema.inference import (
    SYSTEM_FIELD_NAMES,
    field_name_map,
    parent_of,
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


def selected_field_names(key_specs: Iterable[KeySpec]) -> dict[str, str]:
    """Resolve Typesense field names for the selected, non-system keys.

    Returns a ``dotted_key -> field_name`` mapping using leaf-based naming with
    collection-scoped disambiguation for substantially different collisions.
    """
    selected = [s for s in key_specs if s.selected and not s.is_system]
    return field_name_map(selected)


def selected_field_types(key_specs: Iterable[KeySpec]) -> dict[str, str]:
    """Return a ``dotted_key -> Typesense datatype`` map for selected keys."""
    return {
        s.dotted_key: s.datatype
        for s in key_specs
        if s.selected and not s.is_system
    }


def _coerce_value(value, datatype: str):
    """Coerce a metadata value so Typesense accepts it for ``datatype``.

    Typesense rejects a whole document if any value's shape does not match its
    declared field type (e.g. a nested list stored in a ``string[]`` field, or
    a mixed-kind array). For scalar ``string`` fields we JSON-serialise any
    non-string value; for ``string[]`` fields we stringify each element that is
    not already a plain string. Numeric/bool fields pass through. Returning a
    compatible value here prevents silent whole-document import failures.
    """
    if datatype == "string":
        if isinstance(value, str):
            return value
        return json.dumps(value, default=str, sort_keys=True)
    if datatype == "string[]":
        if not isinstance(value, (list, tuple)):
            return [value if isinstance(value, str) else json.dumps(value, default=str)]
        out = []
        for v in value:
            out.append(v if isinstance(v, str) else json.dumps(v, default=str))
        return out
    return value


def build_document(
    uuid: str,
    collection: str,
    metadata: dict,
    field_names: dict[str, str],
    field_types: dict[str, str] | None = None,
    structure_family: str | None = None,
    specs: list[str] | None = None,
) -> dict:
    """Build a single Typesense document from a record's metadata.

    Always includes system fields ``uuid``, ``collection`` and ``tiled_key``.
    ``collection`` is normalized so a Tiled object maps to exactly one document
    ``id``. ``tiled_key`` equals ``id`` and is used to reload the full record
    from Tiled, e.g. ``client["pokemon/{uuid}"]``.

    ``field_names`` maps selected dotted keys to their Typesense field names
    (leaf-based, e.g. ``bmm.detectors.pilatus100k.size`` -> ``size``). The
    original path prefix of each stored key is recorded under ``_parents`` so a
    leaf field name can be traced back to its metadata origin. ``field_types``
    maps the same dotted keys to their declared Typesense datatype so each value
    can be coerced to a compatible shape (nested/mixed structures are
    JSON-stringified) rather than causing the whole document to be rejected.
    """
    field_types = field_types or {}
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

    parents: dict[str, str] = {}
    flat = flatten(dict(metadata or {}))
    for dotted, value in flat.items():
        field_name = field_names.get(dotted)
        if field_name is None:
            continue
        if field_name in SYSTEM_FIELD_NAMES:
            continue
        doc[field_name] = _coerce_value(value, field_types.get(dotted, "string"))
        parent = parent_of(dotted)
        if parent:
            parents[field_name] = parent
    if parents:
        doc["_parents"] = json.dumps(parents, sort_keys=True)
    return doc


def documents_from_container(
    container_client,
    collection: str,
    key_specs: Iterable[KeySpec],
    limit: int = 100,
) -> list[dict]:
    """Produce Typesense documents for every record in a container."""
    key_specs = list(key_specs)
    field_names = selected_field_names(key_specs)
    field_types = selected_field_types(key_specs)
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
                field_names=field_names,
                field_types=field_types,
                structure_family=structure_family,
                specs=specs,
            )
        )
    return docs


class ImportError_(RuntimeError):
    """Raised when one or more documents fail to import into Typesense."""

    def __init__(self, failures: list[dict], total: int):
        self.failures = failures
        self.total = total
        sample = "; ".join(
            str(f.get("error", "unknown")) for f in failures[:3]
        )
        super().__init__(
            f"{len(failures)}/{total} documents failed to import: {sample}"
        )


def import_documents(
    ts_client, index_name: str, documents: list[dict], raise_on_error: bool = True
) -> int:
    """Upsert documents into Typesense. Returns the count actually imported.

    Typesense's ``import_`` returns a per-document result list and does *not*
    raise when individual documents are rejected (e.g. a value whose type does
    not match the inferred schema field). Previously those failures were
    silently swallowed and the function reported every document as imported,
    which made searches return nothing against an empty collection. We now
    inspect each result: by default any failure raises :class:`ImportError_`
    carrying the per-document errors; set ``raise_on_error=False`` to instead
    return only the count that succeeded.
    """
    if not documents:
        return 0
    results = ts_client.collections[index_name].documents.import_(
        documents, {"action": "upsert"}
    )
    failures = [r for r in results if not r.get("success", False)]
    succeeded = len(results) - len(failures)
    if failures and raise_on_error:
        raise ImportError_(failures, len(results))
    return succeeded


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
