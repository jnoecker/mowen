"""FastAPI application factory and entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from mowen_server.config import Settings, get_settings
from mowen_server.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise database. Shutdown: nothing special."""
    settings = getattr(app.state, "settings", None) or get_settings()
    init_db(settings.database_url)
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return the FastAPI application."""
    import mowen

    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="mowen",
        description="Authorship attribution toolkit — API",
        version=mowen.__version__,
        lifespan=lifespan,
    )

    # Store settings on app state so the lifespan hook can access them
    # without calling get_settings() again (important for tests that
    # override settings).
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from mowen_server.routers import corpora, documents, experiments, pipeline, sample_corpora

    app.include_router(documents.router)
    app.include_router(corpora.router)
    app.include_router(experiments.router)
    app.include_router(pipeline.router)
    app.include_router(sample_corpora.router)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    # Try to find the built frontend
    # Look in: 1) ../web/dist (dev), 2) bundled package data
    static_dir = Path(__file__).resolve().parent.parent.parent.parent / "web" / "dist"
    if static_dir.is_dir():
        # Serve static assets
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="static")

        # Catch-all: serve index.html for SPA client-side routing
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Don't intercept API or OpenAPI documentation routes
            if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
                raise HTTPException(status_code=404)
            file_path = static_dir / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()


def run() -> None:
    """Entry point for `mowen-server` console script."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "mowen_server.main:app",
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    run()
