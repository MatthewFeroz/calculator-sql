"""Focused unit tests for defensive branches in the user service."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.schemas.user import UserCreate
from app.services.users import DuplicateUserError, create_user


def test_create_user_translates_database_race_to_domain_error() -> None:
    """A late unique-constraint race is rolled back and reported consistently."""

    database = MagicMock()
    database.scalar.return_value = None
    database.flush.side_effect = IntegrityError(
        "duplicate key", params={}, orig=Exception("unique constraint")
    )
    user_data = UserCreate(
        username="race_user",
        email="race@example.com",
        password="SecurePass123",
    )

    with pytest.raises(DuplicateUserError, match="already registered"):
        create_user(database, user_data)

    database.add.assert_called_once()
    database.rollback.assert_called_once_with()

