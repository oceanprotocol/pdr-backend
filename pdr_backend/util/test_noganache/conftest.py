from typing import List
from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.ppss import (
    mock_ppss,
)

from pdr_backend.models.prediction import mock_prediction, Prediction

from pdr_backend.util.test_data import (
    sample_first_predictions,
    sample_second_predictions,
    sample_daily_predictions,
)


@enforce_types
@pytest.fixture(scope="session")
def _mock_ppss(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("my_tmpdir")
    ppss = mock_ppss("5m", ["binance c BTC/USDT"], "sapphire-mainnet", str(tmpdir))
    return ppss


@enforce_types
@pytest.fixture(scope="session")
def _sample_first_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple)
        for prediction_tuple in sample_first_predictions
    ]


@enforce_types
@pytest.fixture(scope="session")
def _sample_second_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple)
        for prediction_tuple in sample_second_predictions
    ]


@enforce_types
@pytest.fixture(scope="session")
def _sample_daily_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple)
        for prediction_tuple in sample_daily_predictions
    ]
