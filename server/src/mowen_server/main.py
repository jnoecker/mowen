"""FastAPI application factory and entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mowen_server.config import get_settings
from mowen_server.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise database. Shutdown: nothing special."""
    settings = get_settings()
    init_db(settings.database_url)
    yield


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    app = FastAPI(
        title="mowen",
        description="Authorship attribution toolkit — API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from mowen_server.routers import corpora, documents, experiments, pipeline

    app.include_router(documents.router)
    app.include_router(corpora.router)
    app.include_router(experiments.router)
    app.include_router(pipeline.router)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

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
