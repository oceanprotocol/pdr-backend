import csv
import os

from pdr_backend.subgraph.prediction import mock_daily_predictions
from pdr_backend.util.csvs import save_analysis_csv, save_prediction_csv


def test_save_analysis_csv(tmpdir):
    predictions = mock_daily_predictions()
    key = (
        predictions[0].pair.replace("/", "-")
        + predictions[0].timeframe
        + predictions[0].source
    )
    save_analysis_csv(predictions, str(tmpdir))

    with open(os.path.join(str(tmpdir), key + ".csv")) as f:
        data = csv.DictReader(f)
        data_rows = list(data)

    assert data_rows[0]["Predicted Value"] == str(predictions[0].predvalue)
    assert data_rows[0]["True Value"] == str(predictions[0].truevalue)
    assert data_rows[0]["Timestamp"] == str(predictions[0].timestamp)
    assert list(data_rows[0].keys()) == [
        "PredictionID",
        "Timestamp",
        "Slot",
        "Stake",
        "Wallet",
        "Payout",
        "True Value",
        "Predicted Value",
    ]


def test_save_prediction_csv(tmpdir):
    predictions = mock_daily_predictions()
    key = (
        predictions[0].pair.replace("/", "-")
        + predictions[0].timeframe
        + predictions[0].source
    )
    save_prediction_csv(predictions, str(tmpdir))

    with open(os.path.join(str(tmpdir), key + ".csv")) as f:
        data = csv.DictReader(f)
        data_rows = list(row for row in data)

    assert data_rows[0]["Predicted Value"] == str(predictions[0].predvalue)
    assert data_rows[0]["True Value"] == str(predictions[0].truevalue)
    assert data_rows[0]["Timestamp"] == str(predictions[0].timestamp)
    assert list(data_rows[0].keys()) == [
        "Predicted Value",
        "True Value",
        "Timestamp",
        "Stake",
        "Payout",
    ]
