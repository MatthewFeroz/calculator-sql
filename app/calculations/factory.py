"""Factory and operation strategies for supported calculation types."""

from abc import ABC, abstractmethod

from app.calculations.types import CalculationType, parse_calculation_type
from app.operations import add, divide, multiply, subtract


class CalculationOperation(ABC):
    """Common interface implemented by every arithmetic strategy."""

    @abstractmethod
    def calculate(self, a: float, b: float) -> float:
        """Compute a result from two validated operands."""


class AddOperation(CalculationOperation):
    """Add the second operand to the first."""

    def calculate(self, a: float, b: float) -> float:
        return float(add(a, b))


class SubtractOperation(CalculationOperation):
    """Subtract the second operand from the first."""

    def calculate(self, a: float, b: float) -> float:
        return float(subtract(a, b))


class MultiplyOperation(CalculationOperation):
    """Multiply the two operands."""

    def calculate(self, a: float, b: float) -> float:
        return float(multiply(a, b))


class DivideOperation(CalculationOperation):
    """Divide the first operand by the nonzero second operand."""

    def calculate(self, a: float, b: float) -> float:
        return divide(a, b)


class CalculationFactory:
    """Instantiate the strategy corresponding to a calculation type."""

    _operations: dict[CalculationType, type[CalculationOperation]] = {
        CalculationType.ADD: AddOperation,
        CalculationType.SUBTRACT: SubtractOperation,
        CalculationType.MULTIPLY: MultiplyOperation,
        CalculationType.DIVIDE: DivideOperation,
    }

    @classmethod
    def create(cls, calculation_type: CalculationType | str) -> CalculationOperation:
        """Create the correct operation object for the supplied type."""

        canonical_type = parse_calculation_type(calculation_type)
        return cls._operations[canonical_type]()

    @classmethod
    def calculate(
        cls,
        calculation_type: CalculationType | str,
        a: float,
        b: float,
    ) -> float:
        """Select an operation and compute its result through one interface."""

        return cls.create(calculation_type).calculate(a, b)
