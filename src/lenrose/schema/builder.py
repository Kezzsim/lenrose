"""Build a Typesense collection schema from selected KeySpecs."""

from __future__ import annotations

from lenrose.schema.inference import (
    SYSTEM_FIELD_NAMES,
    SYSTEM_FIELDS,
    field_name_map,
    normalize_type,
)
from lenrose.state.models import KeySpec


def build_schema(index_name: str, key_specs: list[KeySpec]) -> dict:
    """Assemble a Typesense collection schema.

    System fields (uuid, collection, tiled_key, viewer hints) are always
    injected. ``collection`` is always a facet. User-selected keys are appended
    using leaf-based field names (with collection-scoped disambiguation for
    substantially different collisions) resolved over the full selected set.
    """
    fields: list[dict] = [dict(f) for f in SYSTEM_FIELDS]

    selected = [s for s in key_specs if s.selected]
    names = field_name_map(selected)
    seen: set[str] = set()
    for spec in selected:
        field_name = names[spec.dotted_key]
        if field_name in SYSTEM_FIELD_NAMES:
            # never let a user key clobber a system field
            continue
        if field_name in seen:
            # colliding leaves that record the field identically share one field
            continue
        seen.add(field_name)
        fields.append(
            {
                "name": field_name,
                "type": normalize_type(spec.datatype),
                "facet": spec.is_facet,
                "index": spec.is_index,
                "optional": True,
            }
        )

    return {
        "name": index_name,
        "fields": fields,
        "enable_nested_fields": False,
    }


def system_key_specs() -> list[KeySpec]:
    """Return the locked system KeySpecs to persist alongside user selections."""
    specs: list[KeySpec] = []
    for f in SYSTEM_FIELDS:
        specs.append(
            KeySpec(
                dotted_key=f["name"],
                datatype=f["type"],
                is_facet=f.get("facet", False),
                is_index=f.get("index", True),
                is_searchable=f["type"].startswith("string"),
                is_system=True,
                selected=True,
            )
        )
    return specs
