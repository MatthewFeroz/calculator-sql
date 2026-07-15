"""SQLAlchemy engine, session, and declarative-base configuration.

The engine owns the database connection pool.  ``SessionLocal`` creates short-
lived units of work that callers must close after use, while ``Base`` provides
the shared SQLAlchemy metadata used by every ORM model in the application.
"""

from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Docker Compose overrides this value so the application connects to the ``db``
# service.  The localhost default is convenient when PostgreSQL is exposed on
# port 5432 during development.
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg2://postgres:postgres@localhost:5432/fastapi_db"
)


class Base(DeclarativeBase):
    """Shared base class whose metadata collects all application tables."""


def get_database_url() -> str:
    """Return the configured SQLAlchemy URL without logging its credentials."""

    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_database_engine(database_url: str | None = None) -> Engine:
    """Build an engine for PostgreSQL or SQLite.

    SQLite is used by lightweight application tests.  Its driver normally
    restricts connections to one thread, so the explicit option allows
    FastAPI's test client to use the same engine safely.
    """

    url = database_url or get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory with explicit transaction boundaries."""

    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# Application-wide objects are created once so SQLAlchemy can reuse its pool.
engine = create_database_engine()
SessionLocal = create_session_factory(engine)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session and guarantee that it is closed afterward.

    This generator is ready for FastAPI's ``Depends`` mechanism in later
    modules.  Closing returns the connection to the engine's pool even when a
    request raises an exception.
    """

    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()

