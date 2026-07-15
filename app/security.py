"""Password hashing and verification helpers.

Passwords are hashed with bcrypt, which automatically embeds a random salt and
work factor in every stored hash.  Verification compares a candidate password
to that encoded hash without ever decrypting or recovering the original value.
"""

import bcrypt


BCRYPT_ROUNDS = 12
MAX_BCRYPT_BYTES = 72


def _password_bytes(plain_password: str) -> bytes:
    """Encode and validate a plaintext password before passing it to bcrypt."""

    if not isinstance(plain_password, str):
        raise TypeError("password must be a string")
    encoded = plain_password.encode("utf-8")
    if not encoded:
        raise ValueError("password must not be empty")
    if len(encoded) > MAX_BCRYPT_BYTES:
        # bcrypt is defined only for the first 72 bytes.  Rejecting longer input
        # prevents two different passwords from ever sharing a truncated value.
        raise ValueError("password must be at most 72 UTF-8 bytes")
    return encoded


def hash_password(plain_password: str) -> str:
    """Return a salted bcrypt hash suitable for the ``password_hash`` column."""

    encoded = _password_bytes(plain_password)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(encoded, salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return whether a plaintext candidate matches a stored bcrypt hash.

    Malformed or non-bcrypt stored values are treated as failed authentication
    instead of surfacing library errors to an API caller.
    """

    try:
        candidate = _password_bytes(plain_password)
        return bcrypt.checkpw(candidate, password_hash.encode("utf-8"))
    except (AttributeError, TypeError, ValueError):
        return False

