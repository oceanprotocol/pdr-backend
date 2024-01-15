from unittest.mock import patch

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.analytics.get_traction_info import get_traction_info_main
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override
from pdr_backend.util.timeutil import timestr_to_ut
from pdr_backend.lake.table_pdr_predictions import (
    _object_list_to_df,
    predictions_schema,
)


@enforce_types
@patch("pdr_backend.analytics.get_traction_info.get_traction_statistics")
@patch("pdr_backend.analytics.get_traction_info.plot_traction_cum_sum_statistics")
@patch("pdr_backend.analytics.get_traction_info.plot_traction_daily_statistics")
@patch("pdr_backend.analytics.get_traction_info.GQLDataFactory.get_gql_dfs")
def test_get_traction_info_main_mainnet(
    mock_predictions_df,
    mock_plot_daily,
    mock_plot_cumsum,
    mock_traction_stat,
    _sample_daily_predictions,
    tmpdir,
    monkeypatch,
):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))
    predictions_df = _object_list_to_df(_sample_daily_predictions, predictions_schema)

    mock_predictions_df.return_value = {"pdr_predictions": predictions_df}

    st_timestr = "2023-11-02"
    fin_timestr = "2023-11-05"

    get_traction_info_main(ppss, st_timestr, fin_timestr, "parquet_data/")

    # calculate ms locally so we can filter raw Predictions
    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= timestr_to_ut(st_timestr) / 1000)
        & (predictions_df["timestamp"] <= timestr_to_ut(fin_timestr) / 1000)
    )

    # Assert calls and values
    pl.DataFrame.equals(mock_traction_stat.call_args, preds_df)
    mock_plot_cumsum.assert_called()
    mock_plot_daily.assert_called()


@enforce_types
@patch("pdr_backend.analytics.get_traction_info.GQLDataFactory.get_gql_dfs")
def test_get_traction_info_empty(
    mock_predictions_df,
    tmpdir,
    capfd,
):
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    mock_predictions_df.return_value = {"pdr_predictions": pl.DataFrame()}
    st_timestr = "2023-11-02"
    fin_timestr = "2023-11-05"

    get_traction_info_main(ppss, st_timestr, fin_timestr, "parquet_data/")

    assert (
        "No records found. Please adjust start and end times inside ppss.yaml."
        in capfd.readouterr().out
    )
