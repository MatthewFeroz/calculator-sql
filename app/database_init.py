"""Helpers for creating the SQLAlchemy tables required by the application."""

from sqlalchemy.engine import Engine

from app.database import Base, engine

# Importing the model registers its table with ``Base.metadata``.  The import is
# intentionally retained even though the name is not referenced directly.
from app.models.user import User  # noqa: F401


def init_db(database_engine: Engine = engine) -> None:
    """Create missing tables without deleting or rewriting existing data."""

    Base.metadata.create_all(bind=database_engine)


if __name__ == "__main__":  # pragma: no cover - exercised as an operator command
    init_db()

