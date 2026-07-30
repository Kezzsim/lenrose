"""Helpers for mapping discovered keys into Typesense schema fields."""

from __future__ import annotations

# Reserved system fields present in every Lenrose document regardless of the
# user's key selections. ``collection`` is the source Tiled container path and
# is faceted by default so records can be filtered by where they came from.
# ``tiled_key`` is ``{collection}/{uuid}`` and is used to load the full record
# from Tiled, e.g. ``client["bmm/{uuid}"]``.
SYSTEM_FIELDS: list[dict] = [
    {"name": "uuid", "type": "string", "facet": False, "index": True},
    {"name": "collection", "type": "string", "facet": True, "index": True},
    {"name": "tiled_key", "type": "string", "facet": False, "index": True},
    # Viewer capability hints, stored so the frontend can decide how to render.
    {"name": "structure_family", "type": "string", "facet": True, "index": True,
     "optional": True},
    {"name": "specs", "type": "string[]", "facet": True, "index": True,
     "optional": True},
]

SYSTEM_FIELD_NAMES = {f["name"] for f in SYSTEM_FIELDS}

VALID_TYPESENSE_TYPES = {
    "string",
    "int32",
    "int64",
    "float",
    "bool",
    "string[]",
    "int64[]",
    "float[]",
    "bool[]",
}


def sanitize_field_name(dotted_key: str) -> str:
    """Convert a dotted metadata key into a Typesense-safe field name.

    Typesense field names must not contain dots; we replace them with a double
    underscore separator that is reversible for display.
    """
    return dotted_key.replace(".", "__")


def desanitize_field_name(field_name: str) -> str:
    return field_name.replace("__", ".")


def normalize_type(datatype: str) -> str:
    """Coerce an inferred datatype to a valid Typesense type, defaulting to string."""
    return datatype if datatype in VALID_TYPESENSE_TYPES else "string"
