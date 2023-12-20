import pytest

from pdr_backend.contract.prediction import (
    mock_daily_predictions,
    mock_first_predictions,
    mock_second_predictions,
)


@pytest.fixture()
def _sample_first_predictions():
    return mock_first_predictions()


@pytest.fixture()
def _sample_second_predictions():
    return mock_second_predictions()


@pytest.fixture()
def _sample_daily_predictions():
    return mock_daily_predictions()
