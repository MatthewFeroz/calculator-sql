"""Calculation business logic independent of future HTTP route handling."""

from sqlalchemy.orm import Session

from app.calculations import CalculationFactory
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationCreate


class UserNotFoundError(ValueError):
    """Raised when a calculation references an unknown user account."""


def create_calculation(
    database: Session,
    user_id: int,
    calculation_data: CalculationCreate,
) -> Calculation:
    """Compute, stage, and refresh a validated calculation record.

    The factory is the only place that selects operation behavior.  As with
    user creation, the caller controls the final transaction commit.
    """

    if database.get(User, user_id) is None:
        raise UserNotFoundError(f"user {user_id} does not exist")

    result = CalculationFactory.calculate(
        calculation_data.type,
        calculation_data.a,
        calculation_data.b,
    )
    calculation = Calculation(
        user_id=user_id,
        a=calculation_data.a,
        b=calculation_data.b,
        type=calculation_data.type,
        result=result,
    )
    database.add(calculation)
    database.flush()
    database.refresh(calculation)
    return calculation
