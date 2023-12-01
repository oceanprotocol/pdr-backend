from unittest.mock import Mock, patch

import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.util.get_predictoor_traction_info import get_predictoor_traction_info_main
from pdr_backend.util.subgraph_predictions import FilterMode

from pdr_backend.util.subgraph_predictions import (
    Prediction,
)

sample_predictions = [
    Prediction(
        id="1",
        pair="ADA/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=False,
        timestamp=1701503000,
        source="binance",
        payout=0.0,
        slot=1701503100,
        user="0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        id="2",
        pair="BTC/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1701589400,
        source="binance",
        payout=0.0,
        slot=1701589500,
        user="0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    )
]


@pytest.fixture(name="mock_ppss_")
def mock_ppss(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")
    ppss.web3_pp = Mock()
    return ppss


@patch("pdr_backend.util.get_predictoor_traction_info.get_predictoor_traction_statistics")
@patch("pdr_backend.util.get_predictoor_traction_info.get_all_contract_ids_by_owner")
@patch("pdr_backend.util.get_predictoor_traction_info.fetch_filtered_predictions")
@patch("pdr_backend.util.get_predictoor_traction_info.plot_predictoor_traction_cum_sum_statistics")
@patch("pdr_backend.util.get_predictoor_traction_info.plot_predictoor_traction_daily_statistics")
def test_get_predictoor_traction_info_main_mainnet(
    mock_plot_predictoor_traction_daily_statistics,
    mock_plot_predictoor_traction_cum_sum_statistics,
    mock_fetch_filtered_predictions,
    mock_get_all_contract_ids_by_owner,
    mock_get_predictoor_traction_statistics,
    mock_ppss_,
):
    mock_ppss_.web3_pp.network = "main"
    mock_get_all_contract_ids_by_owner.return_value = ["0x123", "0x234"]
    mock_fetch_filtered_predictions.return_value = sample_predictions
    
    get_predictoor_traction_info_main(mock_ppss_, "0x123", "2023-01-01", "2023-01-02", "csvs/")

    mock_fetch_filtered_predictions.assert_called_with(
        1672531200,
        1672617600,
        ["0x123"],
        "mainnet",
        FilterMode.CONTRACT,
        payout_only=False,
        trueval_only=False,
    )
    mock_get_predictoor_traction_statistics.assert_called_with(sample_predictions)
    mock_plot_predictoor_traction_cum_sum_statistics.assert_called()
    mock_plot_predictoor_traction_daily_statistics.assert_called()
