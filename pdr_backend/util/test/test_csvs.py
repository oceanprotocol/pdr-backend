import unittest
from unittest.mock import patch, mock_open
from pdr_backend.util.csvs import write_csv
import os


class PredictionMock:
    def __init__(
        self, pair, timeframe, source, timestamp, prediction, trueval, stake, payout
    ):
        self.pair = pair
        self.timeframe = timeframe
        self.source = source
        self.timestamp = timestamp
        self.prediction = prediction
        self.trueval = trueval
        self.stake = stake
        self.payout = payout


class TestWriteCSV(unittest.TestCase):
    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", mock_open())
    def test_write_csv(self, mock_exists, mock_makedirs):
        all_predictions = [
            PredictionMock(
                "BTC/USD", "1h", "binance", 1234567890, 55000.5, 55050.3, 1, 50
            ),
            PredictionMock(
                "BTC/USD", "1h", "binance", 1234567891, 55100.0, 55150.3, 2, 100
            ),
        ]

        csv_output_dir = "some_directory"
        write_csv(all_predictions, csv_output_dir)

        # Check directory creation
        mock_makedirs.assert_called_with(csv_output_dir)

        # Check if file is written correctly
        handle = open("some_directory/BTC-USD1hbinance.csv", "w")
        handle.write.assert_any_call(
            "Predicted Value,True Value,Timestamp,Stake,Payout\n"
        )
        handle.write.assert_any_call("55000.5,55050.3,1234567890,1,50\n")
        handle.write.assert_any_call("55100.0,55150.3,1234567891,2,100\n")


if __name__ == "__main__":
    unittest.main()
