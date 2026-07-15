"""Canonical operation names accepted by the calculation data layer."""

from enum import Enum


class CalculationType(str, Enum):
    """Supported operations as stable, human-readable stored values."""

    ADD = "Add"
    SUBTRACT = "Subtract"
    MULTIPLY = "Multiply"
    DIVIDE = "Divide"
