"""Integration tests for calculations against an actual PostgreSQL database."""

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.calculations import CalculationType
from app.models import Calculation, User
from app.schemas.calculation import CalculationCreate, CalculationRead
from app.services.calculations import UserNotFoundError, create_calculation


pytestmark = pytest.mark.postgres


def persist_user(postgres_session: Session) -> User:
    """Insert the owner required by calculation foreign-key tests."""

    user = User(
        username="calculation_owner",
        email="owner@example.com",
        # Integration tests do not authenticate this fixture account.  The
        # value is deliberately hash-shaped and never contains a raw password.
        password_hash="$2b$12$abcdefghijklmnopqrstuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",
    )
    postgres_session.add(user)
    postgres_session.flush()
    postgres_session.refresh(user)
    return user


@pytest.mark.parametrize(
    "calculation_type, expected_result",
    [
        ("Add", 12.0),
        ("Subtract", 4.0),
        ("Multiply", 32.0),
        ("Divide", 2.0),
    ],
)
def test_create_calculation_persists_each_operation(
    postgres_session: Session,
    calculation_type: str,
    expected_result: float,
) -> None:
    """The service computes and stores every supported operation correctly."""

    user = persist_user(postgres_session)
    calculation = create_calculation(
        postgres_session,
        user.id,
        CalculationCreate(a=8, b=4, type=calculation_type),
    )
    postgres_session.commit()
    postgres_session.expire_all()

    stored = postgres_session.scalar(
        select(Calculation).where(Calculation.id == calculation.id)
    )

    assert stored is not None
    assert stored.user_id == user.id
    assert stored.type is CalculationType(calculation_type)
    assert stored.result == expected_result
    assert stored.created_at is not None
    assert stored.user.username == "calculation_owner"

    public_data = CalculationRead.model_validate(stored).model_dump()
    assert public_data["result"] == expected_result
    assert "user" not in public_data


def test_user_relationship_contains_calculation(postgres_session: Session) -> None:
    """The bidirectional ORM relationship exposes an owner's history."""

    user = persist_user(postgres_session)
    calculation = create_calculation(
        postgres_session,
        user.id,
        CalculationCreate(a=3, b=7, type="Add"),
    )
    postgres_session.commit()

    assert user.calculations == [calculation]
    assert calculation.user is user


def test_service_rejects_unknown_user(postgres_session: Session) -> None:
    """A friendly domain error is raised before PostgreSQL receives an insert."""

    with pytest.raises(UserNotFoundError, match="does not exist"):
        create_calculation(
            postgres_session,
            999_999,
            CalculationCreate(a=1, b=2, type="Add"),
        )

    calculation_count = postgres_session.scalar(
        select(func.count()).select_from(Calculation)
    )
    assert calculation_count == 0


def test_foreign_key_rejects_direct_orphan_insert(
    postgres_session: Session,
) -> None:
    """PostgreSQL protects ownership even when code bypasses the service."""

    postgres_session.add(
        Calculation(
            user_id=999_999,
            a=1.0,
            b=2.0,
            type=CalculationType.ADD,
            result=3.0,
        )
    )

    with pytest.raises(IntegrityError):
        postgres_session.commit()
    postgres_session.rollback()


def test_deleting_user_cascades_to_calculation(postgres_session: Session) -> None:
    """Deleting an account cannot leave orphan calculation history."""

    user = persist_user(postgres_session)
    calculation = create_calculation(
        postgres_session,
        user.id,
        CalculationCreate(a=6, b=3, type="Divide"),
    )
    postgres_session.commit()
    calculation_id = calculation.id

    postgres_session.delete(user)
    postgres_session.commit()
    # This fixture keeps committed objects alive for convenient assertions.
    # Clear that identity cache so the following lookup must query PostgreSQL.
    postgres_session.expunge_all()

    assert postgres_session.get(Calculation, calculation_id) is None


def test_invalid_division_never_reaches_postgres(
    postgres_session: Session,
) -> None:
    """Pydantic rejects a zero divisor before the calculations table changes."""

    persist_user(postgres_session)

    with pytest.raises(ValidationError, match="b must be nonzero"):
        CalculationCreate(a=10, b=0, type="Divide")

    calculation_count = postgres_session.scalar(
        select(func.count()).select_from(Calculation)
    )
    assert calculation_count == 0
