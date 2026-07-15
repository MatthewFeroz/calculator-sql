"""Unit tests for calculation input validation and ORM serialization."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.calculations import CalculationType
from app.models.calculation import Calculation
from app.schemas.calculation import CalculationCreate, CalculationRead


@pytest.mark.parametrize(
    "input_type, expected_type",
    [
        ("Add", CalculationType.ADD),
        ("subtract", CalculationType.SUBTRACT),
        (" MULTIPLY ", CalculationType.MULTIPLY),
        (CalculationType.DIVIDE, CalculationType.DIVIDE),
    ],
)
def test_calculation_create_accepts_supported_operations(
    input_type: str | CalculationType,
    expected_type: CalculationType,
) -> None:
    """All required operation names normalize to the shared enum."""

    calculation = CalculationCreate(a=8, b=2, type=input_type)

    assert calculation.a == 8.0
    assert calculation.b == 2.0
    assert calculation.type is expected_type


@pytest.mark.parametrize("zero", [0, 0.0, -0.0])
def test_calculation_create_rejects_zero_divisor(zero: float) -> None:
    """Every numeric representation of zero is invalid for division."""

    with pytest.raises(ValidationError, match="b must be nonzero"):
        CalculationCreate(a=8, b=zero, type="Divide")


def test_calculation_create_allows_zero_for_non_division() -> None:
    """Zero is a valid operand when the selected operation permits it."""

    calculation = CalculationCreate(a=0, b=0, type="Add")

    assert calculation.a == calculation.b == 0.0


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("type", "Power", "type must be one of"),
        ("a", "8", "valid number"),
        ("b", True, "valid number"),
        ("a", float("nan"), "finite number"),
        ("b", float("inf"), "finite number"),
    ],
    ids=["invalid_type", "numeric_string", "boolean", "nan", "infinity"],
)
def test_calculation_create_rejects_malformed_input(
    field: str,
    value: object,
    expected_error: str,
) -> None:
    """Strict validation prevents malformed values from reaching SQLAlchemy."""

    values: dict[str, object] = {"a": 8, "b": 2, "type": "Add"}
    values[field] = value

    with pytest.raises(ValidationError, match=expected_error):
        CalculationCreate.model_validate(values)


def test_calculation_read_serializes_orm_record() -> None:
    """The public schema exposes stored calculation data and no user object."""

    orm_calculation = Calculation(
        id=17,
        user_id=3,
        a=9.0,
        b=3.0,
        type=CalculationType.DIVIDE,
        result=3.0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    response_data = CalculationRead.model_validate(orm_calculation).model_dump(
        mode="json"
    )

    assert response_data == {
        "id": 17,
        "user_id": 3,
        "a": 9.0,
        "b": 3.0,
        "type": "Divide",
        "result": 3.0,
        "created_at": "2026-01-01T00:00:00Z",
    }
    assert "user" not in response_data
    assert "password_hash" not in response_data
    assert "type='Divide'" in repr(orm_calculation)
