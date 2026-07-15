"""Unit tests for Pydantic user validation and safe serialization."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.user import User
from app.schemas.user import UserCreate, UserRead


def test_user_create_normalizes_identifiers() -> None:
    """Usernames and emails use a canonical lowercase representation."""

    user = UserCreate(
        username="  Alice_123  ",
        email="ALICE@EXAMPLE.COM",
        password="SecurePass123",
    )

    assert user.username == "alice_123"
    assert user.email == "alice@example.com"


@pytest.mark.parametrize(
    "field, value, expected_message",
    [
        ("email", "not-an-email", "valid email address"),
        ("username", "ab", "at least 3 characters"),
        ("username", "has spaces", "only lowercase letters"),
        ("password", "Short1", "at least 8 characters"),
        ("password", "NOLOWERCASE1", "lowercase letter"),
        ("password", "nouppercase1", "uppercase letter"),
        ("password", "NoNumberHere", "contain a number"),
    ],
    ids=[
        "invalid_email",
        "short_username",
        "username_characters",
        "short_password",
        "password_lowercase",
        "password_uppercase",
        "password_number",
    ],
)
def test_user_create_rejects_invalid_data(
    field: str, value: str, expected_message: str
) -> None:
    """Malformed account data fails before a database operation can occur."""

    data = {
        "username": "valid_user",
        "email": "valid@example.com",
        "password": "SecurePass123",
    }
    data[field] = value

    with pytest.raises(ValidationError, match=expected_message):
        UserCreate.model_validate(data)


def test_user_create_rejects_multibyte_password_over_bcrypt_limit() -> None:
    """The 72-byte bcrypt limit is enforced for multibyte Unicode input."""

    with pytest.raises(ValidationError, match="72 UTF-8 bytes"):
        UserCreate(
            username="unicode_user",
            email="unicode@example.com",
            # 24 euro signs occupy 72 bytes, plus the required mixed suffix.
            password=("€" * 24) + "Aa1",
        )


def test_user_read_serializes_orm_object_without_password_hash() -> None:
    """Public responses include account metadata but never credential hashes."""

    orm_user = User(
        id=7,
        username="safe_user",
        email="safe@example.com",
        password_hash="$2b$12$secret-hash-must-not-leak",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    response_data = UserRead.model_validate(orm_user).model_dump()

    assert response_data["id"] == 7
    assert response_data["username"] == "safe_user"
    assert "password" not in response_data
    assert "password_hash" not in response_data

