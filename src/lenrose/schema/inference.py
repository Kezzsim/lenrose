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
    # JSON map of {leaf_field_name: dotted parent path} recording where each
    # leaf-named field came from, since Typesense field names cannot hold dots.
    {"name": "_parents", "type": "string", "facet": False, "index": False,
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


def leaf_of(dotted_key: str) -> str:
    """Return the final segment of a dotted metadata key.

    ``bmm.detectors.pilatus100k.size`` -> ``size``. A key without dots is
    returned unchanged. This leaf is the default Typesense field name, since
    Typesense field names cannot contain the illegal ``.`` character.
    """
    return dotted_key.rsplit(".", 1)[-1]


def parent_of(dotted_key: str) -> str:
    """Return everything preceding the leaf segment, dot-joined.

    ``bmm.detectors.pilatus100k.size`` -> ``bmm.detectors.pilatus100k``. A key
    without dots has an empty parent.
    """
    parts = dotted_key.rsplit(".", 1)
    return parts[0] if len(parts) == 2 else ""


def _scoped_name(dotted_key: str) -> str:
    """A collision-safe field name derived from the full dotted path.

    The whole path is underscore-joined so distinct origins that merely share a
    leaf (e.g. ``start.time`` vs ``stop.time``, or ``start.XDI.Beamline.name``
    vs ``start.XDI.Facility.name``) map to distinct fields and never overwrite
    one another within a single record. Any remaining Typesense-illegal
    characters (only ``.`` is produced by joining) are already removed by the
    underscore join.
    """
    return dotted_key.replace(".", "_")


def field_name_map(specs) -> dict[str, str]:
    """Map each spec's ``dotted_key`` to its Typesense field name.

    The field name is the leaf segment (e.g. ``bmm.detectors.pilatus100k.size``
    -> ``size``) whenever that leaf is unique among the selected keys. Because
    two dotted keys that share a leaf can co-occur in the same record and would
    otherwise overwrite each other (Typesense field names cannot contain the
    illegal ``.``), every key whose leaf is shared by 2+ selected keys is scoped
    to its full underscore-joined path (``start_time``, ``stop_time``,
    ``start_XDI_Beamline_name``). This keeps a unique field per origin.

    ``specs`` is any iterable of objects exposing a ``dotted_key`` attribute
    (e.g. :class:`~lenrose.state.models.KeySpec`).
    """
    specs = list(specs)

    # Group dotted keys by their leaf to detect collisions.
    by_leaf: dict[str, list] = {}
    for spec in specs:
        by_leaf.setdefault(leaf_of(spec.dotted_key), []).append(spec)

    mapping: dict[str, str] = {}
    for leaf, group in by_leaf.items():
        # A leaf shared by more than one selected key can co-occur in a single
        # record; scope every such key by its full path to avoid overwrites.
        collides = len(group) > 1
        for spec in group:
            mapping[spec.dotted_key] = (
                _scoped_name(spec.dotted_key) if collides else leaf
            )
    return mapping


def normalize_type(datatype: str) -> str:
    """Coerce an inferred datatype to a valid Typesense type, defaulting to string."""
    return datatype if datatype in VALID_TYPESENSE_TYPES else "string"
