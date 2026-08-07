# Lenrose

Scientific Metadata Search Engine for [Bluesky Tiled](https://blueskyproject.io/tiled/).

Lenrose ingests metadata from a connected Tiled server via an interactive TUI,
indexes it into [Typesense](https://typesense.org/) with a user-defined schema,
and serves a recomposable React search interface backed by FastAPI.

## Quick start

Lenrose runs as a single command. Bring up the backing services and launch it:

```sh
# Start Typesense + Tiled, then launch Lenrose (setup TUI on first run,
# then the server). This is the one command most users need.
pixi run start
```

`pixi run start` runs the `lenrose` command after ensuring the local Typesense
and Tiled containers are up. On first launch it opens the interactive setup TUI
to ingest metadata; once setup finishes it builds the web frontend (if not
already built) and starts the server. On subsequent launches it detects the
existing configuration and goes straight to serving.

Open the search UI at <http://localhost:8001/> (the API lives under `/api`).

### The `lenrose` command

If the services are already running (or you point at a remote stack via
environment variables), you can invoke Lenrose directly:

```sh
lenrose               # setup-if-needed, build frontend, then serve
lenrose --reconfigure # re-run the setup TUI even if already configured
lenrose --port 9000   # serve on a different port
```

Setup state is stored in SQLite, so Lenrose knows whether it needs to run the
TUI or can start the server immediately. If you quit the setup TUI before it
finishes, the server is not started.

### Development tasks

The following pixi tasks run individual components in isolation, mainly for
development:

```sh
pixi run services-up   # start Typesense + Tiled only
pixi run tui           # run the setup TUI only
pixi run serve         # run the API/server only (uvicorn --reload, port 8001)
pixi run build-web     # build the React frontend into src/lenrose/web/dist
pixi run dev-web       # Vite dev server with hot reload (proxies /api -> 8001)
pixi run dev           # services + Vite dev server
pixi run test          # test suite
```

The `lenrose` command builds the frontend automatically on first run, so
`build-web` is only needed for a standalone `pixi run serve` workflow or when
iterating on the production build.

### Resetting local containers

```sh
# Empty the container CONTENTS (wipe all Typesense collections and the Tiled
# catalog) while keeping the containers running and API keys unchanged.
pixi run services-empty

# Full teardown: stop containers and delete their data volumes.
pixi run services-reset
```

All services share a single, consistent API key across the stack
(`secret` by default; override with `TYPESENSE_API_KEY` / `TILED_API_KEY`).

## Architecture

- **TUI** (Textual): connect to Tiled, select containers + result limits,
  discover metadata keys, choose facets/index options, build the Typesense index.
- **Indexer** (Typesense native client): builds a collection schema from the
  selected keys and upserts flattened metadata documents. Each document stores
  `uuid`, `collection` (source container path, faceted by default), and
  `tiled_key` (`{collection}/{uuid}`) for retrieving the full record from Tiled.
- **Server** (FastAPI + Starlette): serves search configuration (public
  Typesense endpoint + scoped search-only key + the public Tiled API URL) and a
  webhook receiver for live ingestion. It does **not** proxy searches or data.
- **Web** (React + TypeScript + Vite + MUI): search bar, facets, and results.
  Each result lazily loads its data **directly from Tiled** in the browser
  (`src/tiled/`, adapting viewers from bluesky/tiled's web-frontend), previews it
  in the card, and shows a larger interactive viewer in the flyout. A "Streams"
  facet, populated from the Tiled containers of loaded records, selects which
  stream to preview. When Tiled cannot be reached the indexed Typesense fields
  are shown with a warning. For security the browser authenticates to Tiled only
  anonymously or with a user-supplied API key. Follows NSLS-II / BNL branding.
- **State** (SQLite): tracks connections, selected containers, key specs, and
  index state so the app can resume without re-indexing.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `TYPESENSE_HOST` | `localhost` | Typesense host |
| `TYPESENSE_PORT` | `8108` | Typesense port |
| `TYPESENSE_PROTOCOL` | `http` | `http` or `https` |
| `TYPESENSE_API_KEY` | `secret` | Typesense admin API key |
| `LENROSE_DB_PATH` | `state.db` (repo root) | SQLite app state |
| `TILED_API_KEY` | `secret` | Tiled API key (matches the dev stack) |
| `LENROSE_TILED_URI` | _unset_ | Server-internal Tiled URI (used for ingest) |
| `LENROSE_TILED_PUBLIC_URI` | `LENROSE_TILED_URI` | Public Tiled URI the browser uses to load data directly; its `/api/v1` base is sent to the frontend. Tiled must allow the frontend origin via CORS (`server.allow_origins`). |
| `TILED_WEBHOOK_SECRET` | _unset_ | HMAC secret for webhook verification |
