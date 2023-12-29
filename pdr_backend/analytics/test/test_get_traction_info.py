from unittest.mock import Mock, patch

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.analytics.get_traction_info import get_traction_info_main
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override
from pdr_backend.subgraph.subgraph_predictions import FilterMode
from pdr_backend.util.timeutil import timestr_to_ut


@enforce_types
def test_get_traction_info_main_mainnet(
    _sample_daily_predictions,
    tmpdir,
    monkeypatch,
):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    mock_traction_stat = Mock()
    mock_plot_cumsum = Mock()
    mock_plot_daily = Mock()
    mock_getids = Mock(return_value=["0x123"])
    mock_fetch = Mock(return_value=_sample_daily_predictions)

    PATH = "pdr_backend.analytics.get_traction_info"
    PATH2 = "pdr_backend.lake"
    with patch(f"{PATH}.get_traction_statistics", mock_traction_stat), patch(
        f"{PATH}.plot_traction_cum_sum_statistics", mock_plot_cumsum
    ), patch(f"{PATH}.plot_traction_daily_statistics", mock_plot_daily), patch(
        f"{PATH2}.gql_data_factory.get_all_contract_ids_by_owner", mock_getids
    ), patch(
        f"{PATH2}.table_pdr_predictions.fetch_filtered_predictions", mock_fetch
    ):
        st_timestr = "2023-11-02"
        fin_timestr = "2023-11-05"

        get_traction_info_main(ppss, st_timestr, fin_timestr, "parquet_data/")

        mock_fetch.assert_called_with(
            1698883200,
            1699142400,
            ["0x123"],
            "mainnet",
            FilterMode.CONTRACT_TS,
            payout_only=False,
            trueval_only=False,
        )

        # calculate ms locally so we can filter raw Predictions
        st_ut = timestr_to_ut(st_timestr)
        fin_ut = timestr_to_ut(fin_timestr)
        st_ut_sec = st_ut // 1000
        fin_ut_sec = fin_ut // 1000

        # Get all predictions into a dataframe
        preds = [
            x
            for x in _sample_daily_predictions
            if st_ut_sec <= x.timestamp <= fin_ut_sec
        ]
        preds = [pred.__dict__ for pred in preds]
        preds_df = pl.DataFrame(preds)
        preds_df = preds_df.with_columns(
            [
                pl.col("timestamp").mul(1000).alias("timestamp"),
            ]
        )

        # Assert calls and values
        pl.DataFrame.equals(mock_traction_stat.call_args, preds_df)
        mock_plot_cumsum.assert_called()
        mock_plot_daily.assert_called()
