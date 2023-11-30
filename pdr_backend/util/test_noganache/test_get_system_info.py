from unittest.mock import Mock, patch

import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.util.get_system_info import get_system_info_main
from pdr_backend.util.subgraph_predictions import FilterMode


@pytest.fixture(name="mock_ppss_")
def mock_ppss(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")
    ppss.web3_pp = Mock()
    return ppss


@patch("pdr_backend.util.get_system_info.get_system_statistics")
@patch("pdr_backend.util.get_system_info.fetch_filtered_predictions")
def test_get_system_info_main_mainnet(
    mock_fetch_filtered_predictions,
    mock_get_system_statistics,
    mock_ppss_,
):
    mock_ppss_.web3_pp.network = "main"
    mock_fetch_filtered_predictions.return_value = []

    # TODO - Fix get_system_stats() throwing error, use mock instead
    get_system_info_main(
        mock_ppss_,
        ["0x123"],
        "2023-01-01",
        "2023-01-02"
    )

    mock_fetch_filtered_predictions.assert_called_with(
        1672531200,
        1672617600,
        ["0x123"],
        "mainnet",
        FilterMode.CONTRACT,
        payout_only=False,
        trueval_only=False
    )
    mock_get_system_statistics.assert_called_with([])

