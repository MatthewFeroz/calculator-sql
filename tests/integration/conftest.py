"""PostgreSQL fixtures for database integration tests.

These fixtures intentionally require ``TEST_DATABASE_URL``.  This prevents a
test cleanup step from targeting the normal development database by mistake and
makes the real PostgreSQL dependency explicit in local and CI commands.
"""

from collections.abc import Generator
import os

import pytest
from sqlalchemy import create_engine, delete, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models.user import User  # noqa: F401 - registers table metadata


@pytest.fixture(scope="session")
def postgres_engine() -> Generator[Engine, None, None]:
    """Create application tables on the dedicated PostgreSQL test database."""

    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip(
            "TEST_DATABASE_URL is required for PostgreSQL integration tests"
        )

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        engine.dispose()
        pytest.fail(f"PostgreSQL test database is unreachable: {exc}")

    # The CI service database is disposable.  Recreating mapped tables gives the
    # suite a known schema even when a local test database contains stale state.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def postgres_session(postgres_engine: Engine) -> Generator[Session, None, None]:
    """Provide an isolated session and remove committed rows after each test."""

    session_factory = sessionmaker(
        bind=postgres_engine, autoflush=False, expire_on_commit=False
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # Some integration tests deliberately commit to prove persistence and
        # database constraints.  Delete their rows before the next test begins.
        with postgres_engine.begin() as connection:
            connection.execute(delete(User))

