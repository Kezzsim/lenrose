"""Build a Typesense collection schema from selected KeySpecs."""

from __future__ import annotations

from lenrose.schema.inference import (
    SYSTEM_FIELD_NAMES,
    SYSTEM_FIELDS,
    normalize_type,
    sanitize_field_name,
)
from lenrose.state.models import KeySpec


def build_schema(index_name: str, key_specs: list[KeySpec]) -> dict:
    """Assemble a Typesense collection schema.

    System fields (uuid, collection, tiled_key, viewer hints) are always
    injected. ``collection`` is always a facet. User-selected keys are appended.
    """
    fields: list[dict] = [dict(f) for f in SYSTEM_FIELDS]

    for spec in key_specs:
        if not spec.selected:
            continue
        field_name = sanitize_field_name(spec.dotted_key)
        if field_name in SYSTEM_FIELD_NAMES:
            # never let a user key clobber a system field
            continue
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
