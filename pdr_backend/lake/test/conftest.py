import pytest

from pdr_backend.contract.prediction import mock_daily_predictions


@pytest.fixture()
def sample_daily_predictions():
    return mock_daily_predictions()
