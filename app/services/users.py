"""User-account business logic independent of HTTP route handling."""

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.security import hash_password


class DuplicateUserError(ValueError):
    """Raised when a username or email address is already registered."""


def create_user(database: Session, user_data: UserCreate) -> User:
    """Validate uniqueness, hash the password, and stage a new user record.

    ``flush`` sends the INSERT to the database so IDs, timestamps, and unique
    constraints are resolved before the object is returned.  The caller retains
    control over the final transaction commit.
    """

    duplicate_id = database.scalar(
        select(User.id).where(
            or_(User.username == user_data.username, User.email == user_data.email)
        )
    )
    if duplicate_id is not None:
        raise DuplicateUserError("username or email is already registered")

    user = User(
        username=user_data.username,
        email=str(user_data.email),
        password_hash=hash_password(user_data.password),
    )
    database.add(user)

    try:
        # Database constraints still handle simultaneous requests that race
        # between the friendly duplicate check above and this INSERT.
        database.flush()
    except IntegrityError as exc:
        database.rollback()
        raise DuplicateUserError("username or email is already registered") from exc

    database.refresh(user)
    return user

