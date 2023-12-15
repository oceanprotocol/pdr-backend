from typing import List

from enforce_typing import enforce_types
import pytest

from pdr_backend.data_eng.model_factory import ModelFactory
from pdr_backend.models.prediction import (
    Prediction,
    mock_prediction,
)
from pdr_backend.ppss.model_ss import ModelSS
from pdr_backend.util.test_data import (
    sample_first_predictions,
    sample_second_predictions,
    sample_daily_predictions,
)


@pytest.fixture(scope="session")
def model_factory():
    model_ss = ModelSS({"approach": "LIN"})
    return ModelFactory(model_ss)


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
