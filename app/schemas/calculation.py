"""Pydantic validation and serialization schemas for calculations."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.calculations.types import CalculationType, parse_calculation_type


class CalculationCreate(BaseModel):
    """Validated operands and operation accepted by the data layer.

    Strict mode rejects numeric strings instead of silently coercing malformed
    request data.  Integers remain valid numeric inputs and become floats.
    """

    a: float = Field(allow_inf_nan=False)
    b: float = Field(allow_inf_nan=False)
    type: CalculationType

    model_config = ConfigDict(strict=True)

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: object) -> CalculationType:
        """Accept operation names case-insensitively and store one spelling."""

        return parse_calculation_type(value)

    @model_validator(mode="after")
    def reject_zero_divisor(self) -> Self:
        """Reject division by zero before any database work occurs."""

        if self.type is CalculationType.DIVIDE and self.b == 0:
            raise ValueError("b must be nonzero when type is Divide")
        return self


class CalculationRead(BaseModel):
    """Serializable representation of a stored calculation."""

    id: int
    user_id: int
    a: float
    b: float
    type: CalculationType
    result: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, strict=True)
