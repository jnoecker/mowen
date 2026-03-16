"""SQLAlchemy engine, session factory, and base model."""

from collections.abc import Generator

from fastapi import HTTPException
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def init_db(database_url: str) -> None:
    """Create the engine, session factory, and all tables.

    Must be called once at application startup (e.g. in a lifespan hook).
    """
    global engine, SessionLocal  # noqa: PLW0603

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(database_url, connect_args=connect_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    The session is closed automatically when the request finishes.
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialised — call init_db() first")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_404(db: Session, model: type, id: int, label: str = "Resource"):
    """Fetch a row by primary key or raise a 404 HTTPException."""
    obj = db.query(model).filter(model.id == id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return obj
