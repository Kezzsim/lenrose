"""Webhook receiver for live ingestion of new Tiled records.

Implements the receiver side of Tiled webhooks:
https://blueskyproject.io/tiled/user-guide/webhooks.html

Verifies the ``X-Tiled-Signature`` HMAC and deduplicates deliveries via the
``X-Tiled-Event-ID`` header before ingesting the referenced record.

Note: registering webhooks on the Tiled server requires admin scope, HTTPS,
and a server-side ``webhooks:`` config. This endpoint handles delivery only.
"""

from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, HTTPException, Request

from lenrose.config import get_settings
from lenrose.indexer.ingest import build_document, import_documents, make_doc_id, normalize_collection
from lenrose.indexer.typesense_client import get_client
from lenrose.server.tiled_session import get_tiled_client
from lenrose.state import db

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

INGEST_EVENTS = {"container-child-created", "container-child-metadata-updated"}


def verify_signature(body: bytes, secret: str, header: str | None) -> bool:
    if not header:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


@router.post("/tiled")
async def receive(request: Request):
    settings = get_settings()
    body = await request.body()

    # Verify HMAC signature if a secret is configured.
    if settings.tiled_webhook_secret:
        signature = request.headers.get("X-Tiled-Signature")
        if not verify_signature(body, settings.tiled_webhook_secret, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Deduplicate by event id.
    event_id = request.headers.get("X-Tiled-Event-ID")
    if event_id:
        db.init_db()
        if not db.record_seen_event(event_id):
            return {"status": "duplicate", "event_id": event_id}

    payload = await request.json()
    event_type = payload.get("type")
    if event_type not in INGEST_EVENTS:
        return {"status": "ignored", "type": event_type}

    key = payload.get("key")
    path = payload.get("path") or []
    collection = normalize_collection("/".join(str(p) for p in path))
    if not key:
        raise HTTPException(status_code=400, detail="Missing key")

    tiled_key = make_doc_id(collection, key)

    client = get_tiled_client()
    if client is None:
        # Fall back to metadata carried in the webhook payload.
        metadata = payload.get("metadata") or {}
        structure_family = payload.get("structure_family")
        specs = payload.get("specs")
    else:
        try:
            node = client[tiled_key]
            metadata = dict(node.metadata or {})
            structure_family = _as_str(getattr(node, "structure_family", None))
            specs = _specs(getattr(node, "specs", None))
        except Exception:
            metadata = payload.get("metadata") or {}
            structure_family = payload.get("structure_family")
            specs = payload.get("specs")

    specs_list = _specs(specs)
    selected_keys = {s.dotted_key for s in db.load_key_specs() if s.selected and not s.is_system}
    doc = build_document(
        uuid=str(key),
        collection=collection,
        metadata=metadata,
        selected_keys=selected_keys,
        structure_family=structure_family,
        specs=specs_list,
    )
    ts_client = get_client(settings)
    import_documents(ts_client, settings.lenrose_index_name, [doc])
    return {"status": "ingested", "tiled_key": tiled_key}


def _as_str(value):
    return None if value is None else str(value)


def _specs(specs):
    if not specs:
        return None
    return [str(getattr(s, "name", s)) for s in specs]
