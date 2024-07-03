import pytest

from pdr_backend.lake.prediction import (
    mock_first_predictions,
)

from pdr_backend.lake.payout import (
    mock_payouts,
)


@pytest.fixture()
def _sample_first_predictions():
    return mock_first_predictions()


@pytest.fixture()
def _sample_payouts():
    return mock_payouts()
