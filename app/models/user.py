"""SQLAlchemy model for securely persisted user accounts."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """Database representation of one user account.

    Only ``password_hash`` is persisted; there is deliberately no plaintext
    password column.  Unique constraints provide the final, race-safe defense
    against duplicate usernames and email addresses.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(254), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """Return a debugging representation that never exposes credentials."""

        return f"<User id={self.id!r} username={self.username!r}>"

