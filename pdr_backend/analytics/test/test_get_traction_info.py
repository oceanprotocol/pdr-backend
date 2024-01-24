from unittest.mock import patch
import pytest

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.analytics.get_traction_info import get_traction_info_main
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.table_pdr_predictions import (
    _object_list_to_df,
    predictions_schema,
)


@enforce_types
@patch("pdr_backend.analytics.get_traction_info.get_traction_statistics")
@patch("pdr_backend.analytics.get_traction_info.plot_traction_cum_sum_statistics")
@patch("pdr_backend.analytics.get_traction_info.plot_traction_daily_statistics")
@patch("pdr_backend.analytics.get_traction_info.get_slot_statistics")
@patch("pdr_backend.analytics.get_traction_info.plot_slot_daily_statistics")
@patch("pdr_backend.analytics.get_traction_info.GQLDataFactory.get_gql_dfs")
def test_get_traction_info_main_mainnet(
    mock_get_gql_dfs,
    mock_plot_slot_daily_statistics,
    mock_get_slot_statistics,
    mock_plot_traction_daily_statistics,
    mock_plot_traction_cum_sum_statistics,
    mock_get_traction_statistics,
    _sample_daily_predictions,
    tmpdir,
):
    st_timestr = "2023-11-02"
    fin_timestr = "2023-11-07"

    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )
    predictions_df = _object_list_to_df(_sample_daily_predictions, predictions_schema)
    mock_get_gql_dfs.return_value = {"pdr_predictions": predictions_df}
    get_traction_info_main(ppss)

    assert len(predictions_df) > 0

    # calculate ms locally so we can filter raw Predictions
    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp / 1000)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp / 1000)
    )

    assert len(predictions_df) == 6

    # Assert calls and values
    pl.DataFrame.equals(mock_get_traction_statistics.call_args, preds_df)

    # Assert all calls were made
    mock_plot_slot_daily_statistics.assert_called_once()
    mock_get_slot_statistics.assert_called_once()
    mock_plot_traction_daily_statistics.assert_called_once()
    mock_plot_traction_cum_sum_statistics.assert_called_once()
    mock_get_traction_statistics.assert_called_once()


@enforce_types
@patch("pdr_backend.analytics.get_traction_info.GQLDataFactory.get_gql_dfs")
def test_get_traction_info_empty_data_factory(
    mock_predictions_df,
    tmpdir,
):
    st_timestr = "2023-11-02"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    mock_predictions_df.return_value = {"pdr_predictions": pl.DataFrame()}

    with pytest.raises(AssertionError):
        get_traction_info_main(ppss)
