from unittest.mock import Mock, patch

from enforce_typing import enforce_types

from pdr_backend.analytics.get_predictions_info import get_predictions_info_main
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.subgraph.subgraph_predictions import FilterMode


@enforce_types
def test_get_predictions_info_main_mainnet(
    _sample_first_predictions,
    tmpdir,
):
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    mock_getids = Mock(return_value=["0x123", "0x234"])
    mock_fetch = Mock(return_value=_sample_first_predictions)
    mock_save = Mock()
    mock_getstats = Mock()

    PATH = "pdr_backend.analytics.get_predictions_info"
    with patch(f"{PATH}.get_all_contract_ids_by_owner", mock_getids), patch(
        f"{PATH}.fetch_filtered_predictions", mock_fetch
    ), patch(f"{PATH}.save_analysis_csv", mock_save), patch(
        f"{PATH}.get_cli_statistics", mock_getstats
    ):
        st_timestr = "2023-11-02"
        fin_timestr = "2023-11-05"

        get_predictions_info_main(
            ppss, "0x123", st_timestr, fin_timestr, "parquet_data/"
        )

        mock_fetch.assert_called_with(
            1698883200,
            1699142400,
            ["0x123"],
            "mainnet",
            FilterMode.CONTRACT,
            payout_only=True,
            trueval_only=True,
        )
        mock_save.assert_called()
        mock_getstats.assert_called_with(_sample_first_predictions)


@enforce_types
def test_get_predictions_info_empty(tmpdir, capfd):
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    mock_getids = Mock(return_value=[])
    mock_fetch = Mock(return_value={})

    PATH = "pdr_backend.analytics.get_predictions_info"
    with patch(f"{PATH}.get_all_contract_ids_by_owner", mock_getids), patch(
        f"{PATH}.fetch_filtered_predictions", mock_fetch
    ):
        st_timestr = "2023-11-02"
        fin_timestr = "2023-11-05"

        get_predictions_info_main(
            ppss, "0x123", st_timestr, fin_timestr, "parquet_data/"
        )

    assert (
        "No records found. Please adjust start and end times" in capfd.readouterr().out
    )
