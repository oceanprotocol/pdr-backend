from unittest.mock import patch

from pdr_backend.models.prediction import mock_prediction, Prediction

from pdr_backend.util.test_data import (
    sample_first_predictions,
)


@patch("conftest.mock_prediction.Prediction")
def test_mock_predictions():
    predictions = [
        mock_prediction(prediction_tuple)
        for prediction_tuple in sample_first_predictions
    ]

    assert len(predictions) == 2
    assert isinstance(predictions[0], Prediction)
    assert isinstance(predictions[1], Prediction)
    assert predictions[0].id == "1"
    assert predictions[1].id == "2"
