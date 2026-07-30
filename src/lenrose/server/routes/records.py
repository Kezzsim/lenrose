"""Record routes: load full metadata from Tiled via the stored tiled_key."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from lenrose.config import get_settings
from lenrose.indexer.ingest import make_doc_id, normalize_collection
from lenrose.indexer.typesense_client import get_client
from lenrose.server.tiled_session import get_tiled_client

router = APIRouter(prefix="/api", tags=["records"])


@router.get("/records/{uuid}")
def get_record(uuid: str, collection: str | None = Query(None)):
    """Load a record's full metadata from Tiled.

    Disambiguates same-UUID collisions across containers using ``collection``.
    If ``collection`` is omitted, it is resolved from the Typesense document.
    """
    settings = get_settings()

    tiled_key = None
    if collection:
        col = normalize_collection(collection)
        tiled_key = make_doc_id(col, uuid)
    else:
        ts_client = get_client(settings)
        try:
            docs = ts_client.collections[settings.lenrose_index_name].documents.search(
                {"q": uuid, "query_by": "uuid", "filter_by": f"uuid:={uuid}",
                 "per_page": 1}
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        hits = docs.get("hits", [])
        if not hits:
            raise HTTPException(status_code=404, detail="Record not found in index")
        doc = hits[0]["document"]
        tiled_key = doc.get("tiled_key") or make_doc_id(doc["collection"], uuid)
        col = doc["collection"]

    client = get_tiled_client()
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="No active Tiled connection configured on the server.",
        )
    try:
        node = client[tiled_key]
    except Exception as exc:
        raise HTTPException(
            status_code=404, detail=f"Could not load {tiled_key}: {exc}"
        ) from exc

    structure_family = getattr(node, "structure_family", None)
    return {
        "uuid": uuid,
        "collection": col,
        "tiled_key": tiled_key,
        "structure_family": str(structure_family) if structure_family else None,
        "metadata": dict(node.metadata or {}),
    }
