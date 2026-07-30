# Lenrose

Scientific Metadata Search Engine for [Bluesky Tiled](https://blueskyproject.io/tiled/).

Lenrose ingests metadata from a connected Tiled server via an interactive TUI,
indexes it into [Typesense](https://typesense.org/) with a user-defined schema,
and serves a recomposable React search interface backed by FastAPI.

## Quick start

```sh
# 1. Bring up Typesense
pixi run typesense-up

# 2. Ingest metadata interactively
pixi run tui

# 3. Serve the search web app
pixi run serve
```

## Architecture

- **TUI** (Textual): connect to Tiled, select containers + result limits,
  discover metadata keys, choose facets/index options, build the Typesense index.
- **Indexer** (Typesense native client): builds a collection schema from the
  selected keys and upserts flattened metadata documents. Each document stores
  `uuid`, `collection` (source container path, faceted by default), and
  `tiled_key` (`{collection}/{uuid}`) for retrieving the full record from Tiled.
- **Server** (FastAPI + Starlette): search proxy, record retrieval from Tiled,
  and a webhook receiver for live ingestion of new records.
- **Web** (React + TypeScript + Vite + MUI): search bar, facets, results,
  and record detail, following NSLS-II / BNL branding.
- **State** (SQLite): tracks connections, selected containers, key specs, and
  index state so the app can resume without re-indexing.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `TYPESENSE_HOST` | `localhost` | Typesense host |
| `TYPESENSE_PORT` | `8108` | Typesense port |
| `TYPESENSE_PROTOCOL` | `http` | `http` or `https` |
| `TYPESENSE_API_KEY` | `xyz` | Typesense admin API key |
| `LENROSE_DB_PATH` | `~/.local/state/lenrose/state.db` | SQLite app state |
| `TILED_API_KEY` | _unset_ | Tiled API key (optional) |
| `TILED_WEBHOOK_SECRET` | _unset_ | HMAC secret for webhook verification |
