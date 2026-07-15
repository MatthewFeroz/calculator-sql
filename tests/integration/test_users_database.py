"""Integration tests for users against an actual PostgreSQL database."""

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.security import verify_password
from app.services.users import DuplicateUserError, create_user


pytestmark = pytest.mark.postgres


def valid_user_data(**overrides: str) -> UserCreate:
    """Build valid, deterministic user input with optional field overrides."""

    values = {
        "username": "database_user",
        "email": "database@example.com",
        "password": "SecurePass123",
    }
    values.update(overrides)
    return UserCreate.model_validate(values)


def test_create_user_persists_only_a_password_hash(
    postgres_session: Session,
) -> None:
    """The service stores a verifiable salted hash, never the raw password."""

    user_data = valid_user_data()
    user = create_user(postgres_session, user_data)
    postgres_session.commit()

    stored_user = postgres_session.scalar(
        select(User).where(User.username == user_data.username)
    )

    assert stored_user is not None
    assert stored_user.id == user.id
    assert stored_user.password_hash != user_data.password
    assert verify_password(user_data.password, stored_user.password_hash)
    assert stored_user.created_at is not None

    public_data = UserRead.model_validate(stored_user).model_dump()
    assert "password" not in public_data
    assert "password_hash" not in public_data


@pytest.mark.parametrize(
    "duplicate_field, duplicate_value",
    [
        ("username", "database_user"),
        ("email", "database@example.com"),
    ],
    ids=["username", "email"],
)
def test_create_user_rejects_duplicate_identifiers(
    postgres_session: Session, duplicate_field: str, duplicate_value: str
) -> None:
    """The service returns a clear domain error for both unique identifiers."""

    original = create_user(postgres_session, valid_user_data())
    postgres_session.commit()
    assert original.id is not None

    duplicate_data = {
        "username": "second_user",
        "email": "second@example.com",
        "password": "AnotherPass456",
    }
    duplicate_data[duplicate_field] = duplicate_value

    with pytest.raises(DuplicateUserError, match="already registered"):
        create_user(postgres_session, UserCreate.model_validate(duplicate_data))


def test_database_unique_constraint_protects_direct_inserts(
    postgres_session: Session,
) -> None:
    """PostgreSQL itself rejects duplicates that bypass the service layer."""

    password_hash = "$2b$12$abcdefghijklmnopqrstuuuuuuuuuuuuuuuuuuuuuuuuuuuuu"
    postgres_session.add(
        User(
            username="constraint_user",
            email="first@example.com",
            password_hash=password_hash,
        )
    )
    postgres_session.commit()

    postgres_session.add(
        User(
            username="constraint_user",
            email="second@example.com",
            password_hash=password_hash,
        )
    )
    with pytest.raises(IntegrityError):
        postgres_session.commit()
    postgres_session.rollback()


def test_invalid_email_never_reaches_postgres(postgres_session: Session) -> None:
    """Pydantic rejects malformed email input before the users table changes."""

    with pytest.raises(ValidationError, match="valid email address"):
        valid_user_data(email="not-an-email-address")

    user_count = postgres_session.scalar(select(func.count()).select_from(User))
    assert user_count == 0

