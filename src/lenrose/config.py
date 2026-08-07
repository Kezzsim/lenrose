"""Application configuration and settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    """Locate the project root (the directory containing pyproject.toml).

    Falls back to the current working directory if no marker is found, so the
    DB always lands somewhere writable and easy to manage rather than under
    a hidden ~/.local path.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _default_db_path() -> Path:
    return _project_root() / "state.db"


class Settings(BaseSettings):
    """Runtime configuration, populated from the environment."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # Typesense connection
    typesense_host: str = "localhost"
    typesense_port: int = 8108
    typesense_protocol: str = "http"
    # Public-facing Typesense endpoint the browser connects to directly (via the
    # InstantSearch adapter). Defaults to the server-side values when unset.
    typesense_public_host: str | None = None
    typesense_public_port: int | None = None
    typesense_public_protocol: str | None = None
    typesense_api_key: str = "secret"
    # Optional explicit search-only key handed to the browser. When unset, the
    # server mints a scoped search-only key from the admin key at runtime.
    typesense_search_only_key: str | None = None

    # Application state
    lenrose_db_path: Path = _default_db_path()

    # Default Typesense collection (index) name for metadata documents
    lenrose_index_name: str = "lenrose_records"

    # Tiled / webhooks
    #
    # Defaults match the self-contained dev stack (docker-compose.yml and
    # deploy/tiled/entrypoint.sh both fall back to ``secret``) so the backend
    # authenticates against the local Tiled container out of the box.
    tiled_api_key: str | None = "secret"
    tiled_webhook_secret: str | None = None

    @property
    def typesense_nodes(self) -> list[dict]:
        return [
            {
                "host": self.typesense_host,
                "port": self.typesense_port,
                "protocol": self.typesense_protocol,
            }
        ]

    def ensure_db_dir(self) -> None:
        self.lenrose_db_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def typesense_public_node(self) -> dict:
        """Connection details the browser uses to reach Typesense directly."""
        return {
            "host": self.typesense_public_host or self.typesense_host,
            "port": self.typesense_public_port or self.typesense_port,
            "protocol": self.typesense_public_protocol or self.typesense_protocol,
        }


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
