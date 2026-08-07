"""Helpers for locating and building the Vite/React frontend.

The unified ``lenrose`` launcher serves the production build of the web app
from the same origin as the API. This module ensures that build exists,
building it on demand if necessary so a first-time user does not have to run a
separate ``pixi run build-web`` step.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# src/lenrose/web
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
# src/lenrose/web/dist (Vite build.outDir)
WEB_DIST = WEB_DIR / "dist"


def is_frontend_built() -> bool:
    """True if a usable production build is present."""
    return (WEB_DIST / "index.html").exists()


def build_frontend() -> bool:
    """Build the frontend with ``npm install && npm run build``.

    Returns True on success. Returns False (and logs a warning) if npm is not
    available or the build fails, so the server can fall back to API-only mode
    rather than crash.
    """
    npm = shutil.which("npm")
    if npm is None:
        logger.warning(
            "npm not found; cannot build the web frontend. The server will run "
            "API-only. Install Node.js (or run `pixi run build-web`) to enable "
            "the web UI at /."
        )
        return False

    logger.info("Building web frontend in %s (this may take a minute)...", WEB_DIR)
    try:
        subprocess.run([npm, "install"], cwd=WEB_DIR, check=True)
        subprocess.run([npm, "run", "build"], cwd=WEB_DIR, check=True)
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "Web frontend build failed (%s); serving API-only. Run "
            "`pixi run build-web` to diagnose.",
            exc,
        )
        return False

    if not is_frontend_built():
        logger.warning("Web build completed but %s is missing; serving API-only.", WEB_DIST)
        return False

    logger.info("Web frontend built successfully.")
    return True


def ensure_frontend_built() -> bool:
    """Ensure a production build exists, building it if missing.

    Returns True if a build is available (pre-existing or freshly built).
    """
    if is_frontend_built():
        return True
    return build_frontend()
