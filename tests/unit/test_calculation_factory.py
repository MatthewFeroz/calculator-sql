"""Unit tests for calculation operation selection and execution."""

import pytest

from app.calculations.factory import (
    AddOperation,
    CalculationFactory,
    DivideOperation,
    MultiplyOperation,
    SubtractOperation,
)
from app.calculations.types import CalculationType, parse_calculation_type


@pytest.mark.parametrize(
    "calculation_type, operation_class, expected",
    [
        (CalculationType.ADD, AddOperation, 12.0),
        (CalculationType.SUBTRACT, SubtractOperation, 4.0),
        (CalculationType.MULTIPLY, MultiplyOperation, 32.0),
        (CalculationType.DIVIDE, DivideOperation, 2.0),
    ],
    ids=["add", "subtract", "multiply", "divide"],
)
def test_factory_selects_and_executes_each_operation(
    calculation_type: CalculationType,
    operation_class: type,
    expected: float,
) -> None:
    """Each enum value maps to the correct strategy and arithmetic result."""

    operation = CalculationFactory.create(calculation_type)

    assert isinstance(operation, operation_class)
    assert CalculationFactory.calculate(calculation_type, 8.0, 4.0) == expected


def test_factory_accepts_trimmed_case_insensitive_type() -> None:
    """Text input is normalized before the factory selects a strategy."""

    operation = CalculationFactory.create("  multiply  ")

    assert isinstance(operation, MultiplyOperation)
    assert operation.calculate(2.5, 4.0) == 10.0


@pytest.mark.parametrize("invalid_type", ["Power", "", 42, None])
def test_parse_calculation_type_rejects_unknown_values(invalid_type: object) -> None:
    """Unsupported operation values fail with a useful list of choices."""

    with pytest.raises(ValueError, match="Add, Subtract, Multiply, Divide"):
        parse_calculation_type(invalid_type)


def test_factory_division_rejects_zero() -> None:
    """The factory remains safe even when called without a Pydantic schema."""

    with pytest.raises(ValueError, match="Cannot divide by zero"):
        CalculationFactory.calculate(CalculationType.DIVIDE, 10.0, 0.0)
