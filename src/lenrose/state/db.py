"""SQLite-backed application state store."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine, delete, select

from lenrose.config import get_settings
from lenrose.state.models import (
    Connection,
    IndexState,
    KeySpec,
    SeenEvent,
    SelectedContainer,
    WebhookRegistration,
)

__all__ = [
    "Connection",
    "IndexState",
    "KeySpec",
    "SeenEvent",
    "SelectedContainer",
    "WebhookRegistration",
    "get_engine",
    "init_db",
    "session_scope",
    "save_key_specs",
    "load_key_specs",
    "save_containers",
    "load_containers",
    "record_seen_event",
    "upsert_index_state",
    "get_index_state",
    "reset_state_db",
    "has_orphaned_state",
    "reconcile_orphaned_state",
    "save_connection",
    "load_last_connection",
]

_engine = None


def get_engine(db_path: str | None = None):
    """Return (and cache) the SQLModel engine."""
    global _engine
    if _engine is None or db_path is not None:
        settings = get_settings()
        settings.ensure_db_dir()
        path = db_path or str(settings.lenrose_db_path)
        _engine = create_engine(f"sqlite:///{path}", echo=False)
        SQLModel.metadata.create_all(_engine)
    return _engine


def init_db(db_path: str | None = None) -> None:
    engine = get_engine(db_path)
    SQLModel.metadata.create_all(engine)


def session_scope() -> Session:
    return Session(get_engine())


def save_containers(containers: list[SelectedContainer]) -> None:
    with session_scope() as session:
        session.exec(delete(SelectedContainer))
        for c in containers:
            session.add(c)
        session.commit()


def load_containers() -> list[SelectedContainer]:
    with session_scope() as session:
        return list(session.exec(select(SelectedContainer)).all())


def save_key_specs(specs: list[KeySpec]) -> None:
    with session_scope() as session:
        session.exec(delete(KeySpec))
        for s in specs:
            session.add(s)
        session.commit()


def load_key_specs() -> list[KeySpec]:
    with session_scope() as session:
        return list(session.exec(select(KeySpec)).all())


def upsert_index_state(collection_name: str, record_count: int, schema_version: int = 1) -> None:
    with session_scope() as session:
        existing = session.exec(
            select(IndexState).where(IndexState.collection_name == collection_name)
        ).first()
        now = datetime.now(timezone.utc)
        if existing is None:
            existing = IndexState(collection_name=collection_name)
            session.add(existing)
        existing.record_count = record_count
        existing.schema_version = schema_version
        existing.last_ingested = now
        existing.updated_at = now
        session.commit()


def get_index_state(collection_name: str) -> IndexState | None:
    with session_scope() as session:
        return session.exec(
            select(IndexState).where(IndexState.collection_name == collection_name)
        ).first()


def record_seen_event(event_id: str) -> bool:
    """Record an event id. Return True if newly seen, False if a duplicate."""
    with session_scope() as session:
        existing = session.get(SeenEvent, event_id)
        if existing is not None:
            return False
        session.add(SeenEvent(event_id=event_id))
        session.commit()
        return True


def save_connection(
    uri: str,
    auth_method: str = "anonymous",
    username: str | None = None,
    api_key: str | None = None,
    password: str | None = None,
) -> None:
    """Remember the most recent Tiled connection details.

    Persisted immediately on a successful connect so the user does not have to
    re-enter server details if the TUI is closed or quit unexpectedly. Only the
    latest connection is kept (older rows are replaced).
    """
    init_db()
    with session_scope() as session:
        session.exec(delete(Connection))
        session.add(
            Connection(
                uri=uri,
                auth_method=auth_method,
                username=username,
                api_key=api_key,
                password=password,
            )
        )
        session.commit()


def load_last_connection() -> Connection | None:
    """Return the most recently saved Tiled connection, if any."""
    with session_scope() as session:
        return session.exec(
            select(Connection).order_by(Connection.created_at.desc())
        ).first()


def reset_state_db() -> None:
    """Wipe all mutable application state.

    Clears container selections, key specs, index bookkeeping and webhook
    dedup records. Used to recover from a partially-written state left behind
    when the application did not close properly (e.g. selections were persisted
    but the collection was never successfully stored and indexed).

    Saved :class:`Connection` details are intentionally preserved so the user
    does not have to re-enter Tiled server details after a recovery wipe.
    """
    with session_scope() as session:
        session.exec(delete(SelectedContainer))
        session.exec(delete(KeySpec))
        session.exec(delete(IndexState))
        session.exec(delete(WebhookRegistration))
        session.exec(delete(SeenEvent))
        session.commit()


def has_orphaned_state() -> bool:
    """True if selections/key specs exist without any successful IndexState.

    This is the signature of a crashed or improperly closed run: the app
    persisted what the user chose to index, then died before a Typesense
    collection was successfully created and recorded via
    :func:`upsert_index_state`.
    """
    with session_scope() as session:
        has_selection = session.exec(select(SelectedContainer)).first() is not None
        has_specs = session.exec(select(KeySpec)).first() is not None
        indexed = (
            session.exec(
                select(IndexState).where(IndexState.last_ingested.is_not(None))
            ).first()
            is not None
        )
    return (has_selection or has_specs) and not indexed


def reconcile_orphaned_state() -> bool:
    """Wipe orphaned state if a prior run failed before indexing.

    Returns True if a wipe occurred. Call this at startup so the application
    never resumes from a half-written database that would otherwise let the
    same Tiled objects be indexed twice under inconsistent state.
    """
    init_db()
    if has_orphaned_state():
        reset_state_db()
        return True
    return False
