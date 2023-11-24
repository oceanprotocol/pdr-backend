from unittest.mock import Mock, patch

import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.util.get_predictoor_info import get_predictoor_info_main
from pdr_backend.util.subgraph_predictions import FilterMode


@pytest.fixture(name="mock_ppss_")
def mock_ppss(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")
    ppss.web3_pp = Mock()
    return ppss


@patch("pdr_backend.util.get_predictoor_info.fetch_filtered_predictions")
@patch("pdr_backend.util.get_predictoor_info.write_prediction_csv")
@patch("pdr_backend.util.get_predictoor_info.get_cli_statistics")
def test_get_predictoor_info_main_mainnet(
    mock_get_cli_statistics,
    mock_write_prediction_csv,
    mock_fetch_filtered_predictions,
    mock_ppss_,
):
    mock_ppss_.web3_pp.network = "main"
    mock_fetch_filtered_predictions.return_value = []

    get_predictoor_info_main(
        mock_ppss_,
        "0x123",
        "2023-01-01",
        "2023-01-02",
        "/path/to/csv",
    )

    mock_fetch_filtered_predictions.assert_called_with(
        1672531200,
        1672617600,
        ["0x123"],
        "mainnet",
        FilterMode.PREDICTOOR,
    )
    mock_write_prediction_csv.assert_called_with([], "/path/to/csv")
    mock_get_cli_statistics.assert_called_with([])
