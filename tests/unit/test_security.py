"""Unit tests for the password hashing boundary in ``app.security``."""

import pytest

from app.security import hash_password, verify_password


VALID_PASSWORD = "SecurePass123"


def test_hash_password_never_returns_plaintext() -> None:
    """bcrypt output is encoded and never equal to the submitted password."""

    password_hash = hash_password(VALID_PASSWORD)

    assert password_hash != VALID_PASSWORD
    assert password_hash.startswith("$2b$")


def test_hash_password_uses_a_unique_salt_each_time() -> None:
    """The same password receives a fresh random salt for every stored hash."""

    first_hash = hash_password(VALID_PASSWORD)
    second_hash = hash_password(VALID_PASSWORD)

    assert first_hash != second_hash
    assert verify_password(VALID_PASSWORD, first_hash)
    assert verify_password(VALID_PASSWORD, second_hash)


def test_verify_password_rejects_wrong_password() -> None:
    """A valid hash does not authenticate a different plaintext candidate."""

    password_hash = hash_password(VALID_PASSWORD)

    assert verify_password("WrongPass123", password_hash) is False


@pytest.mark.parametrize("stored_hash", ["", "not-a-bcrypt-hash", None])
def test_verify_password_handles_malformed_stored_hash(stored_hash: str | None) -> None:
    """Corrupt credential data fails closed instead of raising an exception."""

    assert verify_password(VALID_PASSWORD, stored_hash) is False  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "invalid_password, error_type",
    [
        ("", ValueError),
        ("a" * 73, ValueError),
        (12345, TypeError),
    ],
    ids=["empty", "over_bcrypt_limit", "not_a_string"],
)
def test_hash_password_rejects_unsafe_input(
    invalid_password: object, error_type: type[Exception]
) -> None:
    """Invalid values are rejected before they reach the bcrypt library."""

    with pytest.raises(error_type):
        hash_password(invalid_password)  # type: ignore[arg-type]

