"""Search configuration route.

The frontend talks to Typesense directly via the InstantSearch adapter, so the
server no longer proxies searches. This module exposes the configuration the
browser needs to bootstrap the adapter: the public Typesense endpoint, a scoped
search-only API key, the collection name, the fields to query, and the facet /
display field metadata derived from the persisted key specs.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from lenrose.config import get_settings
from lenrose.indexer.search_key import get_scoped_search_key
from lenrose.server.tiled_session import server_tiled_summary
from lenrose.state import db

router = APIRouter(prefix="/api", tags=["search"])


def _field_name_map(specs) -> dict[str, str]:
    from lenrose.schema.inference import field_name_map

    return field_name_map([s for s in specs if s.selected])


def _facet_type_map(specs) -> dict[str, str]:
    names = _field_name_map(specs)
    return {
        names[s.dotted_key]: s.datatype
        for s in specs
        if s.dotted_key in names and s.selected
    }


def _facet_fields(specs) -> list[str]:
    names = _field_name_map(specs)
    fields = [
        names[s.dotted_key]
        for s in specs
        if s.is_facet and not s.is_display and s.dotted_key in names
    ]
    fields = list(dict.fromkeys(fields))
    if "collection" not in fields:
        fields.insert(0, "collection")
    return fields


def _query_by(specs) -> list[str]:
    names = _field_name_map(specs)
    searchable = [
        names[s.dotted_key]
        for s in specs
        if s.dotted_key in names
        and s.is_searchable
        and s.is_index
        and s.datatype.startswith("string")
    ]
    fields = list(dict.fromkeys(searchable))
    return fields or ["collection"]


def _display_fields(specs) -> tuple[list[dict], str]:
    names = _field_name_map(specs)
    options = [{"value": "uuid", "label": "UUID", "field": "uuid"}]
    default = "uuid"
    for spec in specs:
        if not spec.selected or not spec.is_display or spec.is_system:
            continue
        field = names.get(spec.dotted_key)
        if field:
            options.append(
                {"value": spec.dotted_key, "label": spec.dotted_key, "field": field}
            )
            default = spec.dotted_key
            break
    return options, default


@router.get("/search-config")
def search_config():
    """Return everything the browser needs to configure InstantSearch."""
    settings = get_settings()
    specs = db.load_key_specs()

    try:
        api_key = get_scoped_search_key(settings)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"Could not mint search key: {exc}"
        ) from exc

    node = settings.typesense_public_node
    facet_types = _facet_type_map(specs)
    display_fields, default_display = _display_fields(specs)

    return {
        "typesense": {
            "host": node["host"],
            "port": node["port"],
            "protocol": node["protocol"],
            "apiKey": api_key,
        },
        "collection": settings.lenrose_index_name,
        "queryBy": _query_by(specs),
        "facets": _facet_fields(specs),
        "facetTypes": facet_types,
        "displayFields": display_fields,
        "defaultDisplay": default_display,
        "tiled": server_tiled_summary(),
    }
