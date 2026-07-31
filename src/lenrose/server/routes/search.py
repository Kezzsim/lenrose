"""Search routes: proxy Typesense searches and expose facet configuration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from lenrose.config import get_settings
from lenrose.indexer.typesense_client import get_client
from lenrose.state import db

router = APIRouter(prefix="/api", tags=["search"])


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
        from lenrose.schema.inference import field_name_map

        names = field_name_map([s for s in specs if s.selected])
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
        params["filter_by"] = filter_by

    try:
        result = client.collections[settings.lenrose_index_name].documents.search(params)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Search failed: {exc}") from exc
    return result


@router.get("/facets")
def facets():
    """Return the default facet fields (collection is always included)."""
    specs = db.load_key_specs()
    from lenrose.schema.inference import field_name_map

    names = field_name_map([s for s in specs if s.selected])
    facet_fields = [
        names[s.dotted_key] for s in specs if s.is_facet and s.dotted_key in names
    ]
    facet_fields = list(dict.fromkeys(facet_fields))
    if "collection" not in facet_fields:
        facet_fields.insert(0, "collection")
    return {"facets": facet_fields}
