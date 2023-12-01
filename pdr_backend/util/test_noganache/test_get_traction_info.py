from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.util.get_traction_info import get_traction_info_main
from pdr_backend.util.subgraph_predictions import FilterMode


@enforce_types
@patch("pdr_backend.util.get_traction_info.get_traction_statistics")
@patch("pdr_backend.util.get_traction_info.get_all_contract_ids_by_owner")
@patch("pdr_backend.util.get_traction_info.fetch_filtered_predictions")
@patch("pdr_backend.util.get_traction_info.plot_traction_cum_sum_statistics")
@patch("pdr_backend.util.get_traction_info.plot_traction_daily_statistics")
def test_get_traction_info_main_mainnet(
    mock_plot_traction_daily_statistics,
    mock_plot_traction_cum_sum_statistics,
    mock_fetch_filtered_predictions,
    mock_get_all_contract_ids_by_owner,
    mock_get_traction_statistics,
    mock_ppss,
    sample_predictions,
):
    mock_ppss.web3_pp.network = "main"
    mock_get_all_contract_ids_by_owner.return_value = ["0x123", "0x234"]
    mock_fetch_filtered_predictions.return_value = sample_predictions

    get_traction_info_main(mock_ppss, "0x123", "2023-01-01", "2023-01-02", "csvs/")

    mock_fetch_filtered_predictions.assert_called_with(
        1672531200,
        1672617600,
        ["0x123"],
        "mainnet",
        FilterMode.CONTRACT,
        payout_only=False,
        trueval_only=False,
    )
    mock_get_traction_statistics.assert_called_with(sample_predictions)
    mock_plot_traction_cum_sum_statistics.assert_called()
    mock_plot_traction_daily_statistics.assert_called()
