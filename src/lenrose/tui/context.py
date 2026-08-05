"""Shared mutable context passed between TUI screens."""

from __future__ import annotations

from dataclasses import dataclass, field

from lenrose.config import Settings, get_settings
from lenrose.state.models import KeySpec, SelectedContainer
from lenrose.tiled_client.auth import TiledConnectionInfo
from lenrose.tiled_client.introspect import ContainerInfo


def _default_settings() -> Settings:
    return get_settings().model_copy()


@dataclass
class IngestContext:
    settings: Settings = field(default_factory=_default_settings)
    connection: TiledConnectionInfo | None = None
    client: object | None = None
    containers: list[ContainerInfo] = field(default_factory=list)
    selected_containers: list[SelectedContainer] = field(default_factory=list)
    key_specs: list[KeySpec] = field(default_factory=list)
