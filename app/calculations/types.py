"""Canonical operation names accepted by the calculation data layer."""

from enum import Enum


class CalculationType(str, Enum):
    """Supported operations as stable, human-readable stored values."""

    ADD = "Add"
    SUBTRACT = "Subtract"
    MULTIPLY = "Multiply"
    DIVIDE = "Divide"


def parse_calculation_type(value: object) -> CalculationType:
    """Return the canonical enum for a case-insensitive operation name.

    Centralizing this conversion keeps the schema and factory in agreement
    about accepted names while still storing one consistent value.
    """

    if isinstance(value, CalculationType):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        for calculation_type in CalculationType:
            if calculation_type.value.casefold() == normalized:
                return calculation_type
    allowed = ", ".join(choice.value for choice in CalculationType)
    raise ValueError(f"type must be one of: {allowed}")
