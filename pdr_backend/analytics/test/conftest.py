import pytest

from pdr_backend.models.prediction import (
    mock_first_predictions,
    mock_second_predictions,
    mock_daily_predictions,
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
