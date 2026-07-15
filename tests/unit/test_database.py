"""Unit tests for reusable SQLAlchemy configuration helpers."""

from unittest.mock import MagicMock

from sqlalchemy import text

import app.database as database_module
from app.database import create_database_engine, create_session_factory, get_database_url
from app.models.user import User


def test_get_database_url_reads_environment(monkeypatch) -> None:
    """Deployment configuration comes from DATABASE_URL when it is present."""

    expected_url = "sqlite+pysqlite:///:memory:"
    monkeypatch.setenv("DATABASE_URL", expected_url)

    assert get_database_url() == expected_url


def test_engine_and_session_factory_execute_query() -> None:
    """Factory-created engines and sessions can perform a database round trip."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session = create_session_factory(engine)()
    try:
        assert session.scalar(text("SELECT 1")) == 1
    finally:
        session.close()
        engine.dispose()


def test_get_db_always_closes_session(monkeypatch) -> None:
    """The dependency generator closes its session after request processing."""

    fake_session = MagicMock()
    monkeypatch.setattr(database_module, "SessionLocal", lambda: fake_session)

    dependency = database_module.get_db()
    assert next(dependency) is fake_session
    dependency.close()

    fake_session.close.assert_called_once_with()


def test_user_repr_excludes_sensitive_fields() -> None:
    """Debug output identifies the account without leaking email or hash data."""

    user = User(
        id=3,
        username="repr_user",
        email="private@example.com",
        password_hash="super-secret-hash",
    )

    representation = repr(user)

    assert representation == "<User id=3 username='repr_user'>"
    assert user.email not in representation
    assert user.password_hash not in representation

