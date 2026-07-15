"""SQLAlchemy model for arithmetic calculations owned by users."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.calculations import CalculationType
from app.database import Base


class Calculation(Base):
    """Persist one validated arithmetic operation and its computed result.

    Results are stored so calculation history can be read without repeating
    work.  The foreign key makes ownership enforceable by PostgreSQL, while
    the relationship lets application code navigate from either side.
    """

    __tablename__ = "calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    a: Mapped[float] = mapped_column(Float, nullable=False)
    b: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[CalculationType] = mapped_column(
        Enum(
            CalculationType,
            name="calculation_type",
            values_callable=lambda choices: [choice.value for choice in choices],
            validate_strings=True,
        ),
        nullable=False,
        index=True,
    )
    result: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="calculations")

    def __repr__(self) -> str:
        """Return a compact representation suitable for debugging."""

        return (
            f"<Calculation id={self.id!r} user_id={self.user_id!r} "
            f"type={self.type.value!r}>"
        )


# Imported after the class for type resolution without a runtime import cycle.
from app.models.user import User  # noqa: E402
