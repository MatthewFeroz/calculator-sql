"""Pydantic validation and serialization schemas for users."""

from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


USERNAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


class UserCreate(BaseModel):
    """Validated input accepted when a user account is created.

    Normalizing identifiers before persistence gives the database one canonical
    representation, so values such as ``Alice`` and ``alice`` cannot become two
    visually identical accounts.
    """

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72, repr=False)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        """Strip surrounding whitespace and normalize usernames to lowercase."""

        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("username")
    @classmethod
    def validate_username_characters(cls, value: str) -> str:
        """Allow portable usernames made from letters, numbers, and underscores."""

        if not USERNAME_PATTERN.fullmatch(value):
            raise ValueError(
                "username may contain only lowercase letters, numbers, and underscores"
            )
        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """Store email addresses in lowercase for consistent uniqueness checks."""

        return str(value).lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Require a mixed password that bcrypt can process without truncation."""

        if len(value.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 UTF-8 bytes")
        if not any(character.islower() for character in value):
            raise ValueError("password must contain a lowercase letter")
        if not any(character.isupper() for character in value):
            raise ValueError("password must contain an uppercase letter")
        if not any(character.isdigit() for character in value):
            raise ValueError("password must contain a number")
        return value


class UserRead(BaseModel):
    """Public user representation; password hashes are intentionally omitted."""

    id: int
    username: str
    email: EmailStr
    created_at: datetime

    # ``from_attributes`` allows direct, type-checked serialization of a
    # SQLAlchemy ``User`` instance without converting it to a dictionary first.
    model_config = ConfigDict(from_attributes=True)

