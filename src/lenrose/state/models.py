"""SQLModel models describing Lenrose application state."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Connection(SQLModel, table=True):
    """A remembered Tiled server connection.

    Persisted so an unexpected quit does not force the user to re-enter their
    server details. Secrets (``api_key``/``password``) are stored locally in the
    project's state DB for convenience; the file is developer-local state and
    should not be committed (see .gitignore).
    """

    id: int | None = Field(default=None, primary_key=True)
    uri: str
    auth_method: str = "anonymous"  # anonymous | api_key | password
    username: str | None = None
    api_key: str | None = None
    password: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class SelectedContainer(SQLModel, table=True):
    """A container the user chose to ingest, with a per-container result limit."""

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)  # e.g. "bmm"
    result_limit: int = 100
    selected: bool = True


class KeySpec(SQLModel, table=True):
    """A discovered metadata key and how it should be indexed in Typesense."""

    id: int | None = Field(default=None, primary_key=True)
    dotted_key: str = Field(index=True)  # e.g. "start.plan_name"
    datatype: str = "string"  # typesense field type
    is_facet: bool = False
    is_index: bool = True
    is_searchable: bool = True
    is_system: bool = False  # locked system fields (uuid, collection, tiled_key)
    selected: bool = True


class IndexState(SQLModel, table=True):
    """Tracks the state of a Typesense collection (index)."""

    id: int | None = Field(default=None, primary_key=True)
    collection_name: str = Field(index=True)  # typesense index name
    schema_version: int = 1
    record_count: int = 0
    last_ingested: datetime | None = None
    updated_at: datetime = Field(default_factory=_utcnow)


class WebhookRegistration(SQLModel, table=True):
    """A webhook registered against a Tiled container path."""

    id: int | None = Field(default=None, primary_key=True)
    container_path: str
    tiled_webhook_id: int | None = None
    target_url: str
    created_at: datetime = Field(default_factory=_utcnow)


class SeenEvent(SQLModel, table=True):
    """Deduplication record for Tiled webhook X-Tiled-Event-ID headers."""

    event_id: str = Field(primary_key=True)
    seen_at: datetime = Field(default_factory=_utcnow)
