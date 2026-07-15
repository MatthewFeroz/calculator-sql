"""Focused unit tests for defensive calculation-service behavior."""

from unittest.mock import MagicMock

import pytest

from app.schemas.calculation import CalculationCreate
from app.services.calculations import UserNotFoundError, create_calculation


def test_create_calculation_rejects_unknown_user_before_computing() -> None:
    """A missing owner produces a domain error and no staged database row."""

    database = MagicMock()
    database.get.return_value = None
    calculation_data = CalculationCreate(a=4, b=2, type="Divide")

    with pytest.raises(UserNotFoundError, match="user 999 does not exist"):
        create_calculation(database, 999, calculation_data)

    database.add.assert_not_called()
    database.flush.assert_not_called()
