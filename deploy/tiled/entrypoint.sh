#!/usr/bin/env bash
#
# Self-contained Tiled bootstrap for local development / CI.
#
# The writable catalog lives entirely on the container's own volume
# (/deploy/data). No host bind mount or pre-existing directory on the host is
# required. A deterministic (alphanumeric) API key is used so the rest of the
# stack can authenticate without manual token juggling.
#
# The catalog starts empty but writable, so records can be ingested at runtime
# via the Tiled client. The `init_if_not_exists` option in config.yml creates
# the catalog schema on first boot.
set -euo pipefail

: "${TILED_API_KEY:=secret}"
export TILED_API_KEY

DATA_ROOT="/deploy/data"
STORAGE_DIR="${DATA_ROOT}/storage"

mkdir -p "${STORAGE_DIR}"

echo "[tiled] Serving on 0.0.0.0:8000 (writable catalog at ${DATA_ROOT})"
exec tiled serve config /deploy/config.yml --host 0.0.0.0 --port 8000
