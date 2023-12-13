from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.util.get_predictions_info import get_predictions_info_main
from pdr_backend.util.subgraph_predictions import FilterMode


@enforce_types
@patch("pdr_backend.util.get_predictions_info.get_cli_statistics")
@patch("pdr_backend.util.get_predictions_info.get_all_contract_ids_by_owner")
@patch("pdr_backend.util.get_predictions_info.fetch_filtered_predictions")
def test_get_predictions_info_main_mainnet(
    mock_fetch_filtered_predictions,
    mock_get_all_contract_ids_by_owner,
    mock_get_cli_statistics,
    mock_ppss,
    sample_first_predictions,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0x123", "0x234"]
    mock_fetch_filtered_predictions.return_value = sample_first_predictions

    st_timestr = "2023-11-02"
    fin_timestr = "2023-11-05"

    get_predictions_info_main(
        mock_ppss, "0x123", st_timestr, fin_timestr, "parquet_data/"
    )

    mock_fetch_filtered_predictions.assert_called_with(
        1698883200,
        1699142400,
        ["0x123"],
        "mainnet",
        FilterMode.CONTRACT,
        payout_only=True,
        trueval_only=True,
    )
    mock_get_cli_statistics.assert_called_with(sample_first_predictions)
