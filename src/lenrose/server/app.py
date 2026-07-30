"""Lenrose FastAPI application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from lenrose.server.routes import records, search, webhooks

_WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Lenrose", description="Scientific Metadata Search Engine")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(search.router)
    app.include_router(records.router)
    app.include_router(webhooks.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    # Serve built frontend if present (SPA fallback to index.html).
    if _WEB_DIST.exists():
        app.mount("/", StaticFiles(directory=str(_WEB_DIST), html=True), name="web")

    return app


app = create_app()


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run("lenrose.server.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
