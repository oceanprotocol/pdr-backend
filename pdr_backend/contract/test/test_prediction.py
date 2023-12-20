from enforce_typing import enforce_types

from pdr_backend.contract.prediction import Prediction, mock_first_predictions


@enforce_types
def test_predictions():
    predictions = mock_first_predictions()

    assert len(predictions) == 2
    assert isinstance(predictions[0], Prediction)
    assert isinstance(predictions[1], Prediction)
    assert (
        predictions[0].ID
        == "ADA/USDT-5m-1701503100-0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    )
    assert (
        predictions[1].ID
        == "BTC/USDT-5m-1701589500-0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    )
