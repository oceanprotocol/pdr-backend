from pdr_backend.models.prediction import mock_prediction, Prediction

from pdr_backend.util.test_data import (
    sample_first_predictions,
)


def test_mock_predictions():
    predictions = [
        mock_prediction(prediction_tuple)
        for prediction_tuple in sample_first_predictions
    ]

    assert len(predictions) == 2
    assert isinstance(predictions[0], Prediction)
    assert isinstance(predictions[1], Prediction)
    assert (
        predictions[0].id
        == "ADA/USDT-5m-1701503100-0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    )
    assert (
        predictions[1].id
        == "BTC/USDT-5m-1701589500-0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    )
