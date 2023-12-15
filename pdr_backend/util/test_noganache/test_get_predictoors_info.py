from unittest.mock import patch

from pdr_backend.util.get_predictoors_info import get_predictoors_info_main
from pdr_backend.util.subgraph_predictions import FilterMode


@patch("pdr_backend.util.get_predictoors_info.fetch_filtered_predictions")
@patch("pdr_backend.util.get_predictoors_info.save_prediction_csv")
@patch("pdr_backend.util.get_predictoors_info.get_cli_statistics")
def test_get_predictoors_info_main_mainnet(
    mock_get_cli_statistics,
    mock_save_prediction_csv,
    mock_fetch_filtered_predictions,
    _mock_ppss,
):
    mock_fetch_filtered_predictions.return_value = []

    get_predictoors_info_main(
        _mock_ppss,
        "0x123",
        "2023-01-01",
        "2023-01-02",
        "parquet_data/",
    )

    mock_fetch_filtered_predictions.assert_called_with(
        1672531200,
        1672617600,
        ["0x123"],
        "mainnet",
        FilterMode.PREDICTOOR,
    )
    mock_save_prediction_csv.assert_called_with([], "parquet_data/")
    mock_get_cli_statistics.assert_called_with([])
