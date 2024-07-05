import pytest

from pdr_backend.lake.prediction import (
    mock_first_predictions,
    mock_daily_predictions,
)
from pdr_backend.lake.payout import (
    mock_payouts,
    mock_payouts_related_with_predictions,
)

@pytest.fixture()
def _sample_first_predictions():
    return mock_first_predictions()

@pytest.fixture()
def _sample_daily_predictions():
    return mock_daily_predictions()

@pytest.fixture()
def _sample_payouts():
    return mock_payouts()

@pytest.fixture()
def _sample_payouts_related_with_predictions():
    return mock_payouts_related_with_predictions()