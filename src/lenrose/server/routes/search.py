"""Search routes: proxy Typesense searches and expose facet configuration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from lenrose.config import get_settings
from lenrose.indexer.typesense_client import get_client
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


def _normalize_bool_filters(filter_by: str | None) -> str | None:
    """Accept stale UI bool filters that quote true/false as strings."""
    if not filter_by:
        return filter_by

    for field, datatype in _facet_type_map(db.load_key_specs()).items():
        if datatype != "bool":
            continue
        filter_by = filter_by.replace(f"{field}:=[`true`]", f"{field}:=true")
        filter_by = filter_by.replace(f"{field}:=[`false`]", f"{field}:=false")
        filter_by = filter_by.replace(f"{field}:=`true`", f"{field}:=true")
        filter_by = filter_by.replace(f"{field}:=`false`", f"{field}:=false")
    return filter_by


@router.get("/search")
def search(
    q: str = Query("*", description="Query string"),
    query_by: str | None = Query(None, description="Comma-separated fields"),
    facet_by: str | None = Query(None),
    filter_by: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=250),
):
    """Proxy a search against the Typesense index."""
    settings = get_settings()
    client = get_client(settings)

    if not query_by:
        # default to searchable string fields recorded in state
        specs = db.load_key_specs()

        names = _field_name_map(specs)
        searchable = [
            names[s.dotted_key]
            for s in specs
            if s.dotted_key in names
            and s.is_searchable
            and s.is_index
            and s.datatype.startswith("string")
        ]
        query_by = ",".join(dict.fromkeys(searchable)) if searchable else "collection"

    params = {
        "q": q,
        "query_by": query_by,
        "page": page,
        "per_page": per_page,
    }
    if facet_by:
        params["facet_by"] = facet_by
    if filter_by:
        params["filter_by"] = _normalize_bool_filters(filter_by)

    try:
        result = client.collections[settings.lenrose_index_name].documents.search(params)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Search failed: {exc}") from exc
    return result


@router.get("/facets")
def facets():
    """Return the default facet fields (collection is always included)."""
    specs = db.load_key_specs()

    names = _field_name_map(specs)
    facet_types = _facet_type_map(specs)
    facet_fields = [
        names[s.dotted_key] for s in specs if s.is_facet and s.dotted_key in names
    ]
    facet_fields = list(dict.fromkeys(facet_fields))
    if "collection" not in facet_fields:
        facet_fields.insert(0, "collection")
    return {"facets": facet_fields, "facet_types": facet_types}
