from unittest.mock import patch
import pytest

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.table_pdr_predictions import (
    _object_list_to_df,
    predictions_schema,
)
from pdr_backend.analytics.get_predictoors_info import get_predictoors_info_main
from pdr_backend.ppss.ppss import mock_ppss


@enforce_types
@patch("pdr_backend.analytics.get_predictoors_info.get_predictoor_summary_stats")
@patch("pdr_backend.analytics.get_predictoors_info.GQLDataFactory.get_gql_dfs")
def test_get_predictoors_info_main_mainnet(
    mock_get_gql_dfs,
    mock_get_predictoor_summary_stats,
    _sample_first_predictions,
    tmpdir,
):
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _object_list_to_df(_sample_first_predictions, predictions_schema)
    mock_get_gql_dfs.return_value = {"pdr_predictions": predictions_df}

    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    get_predictoors_info_main(
        ppss,
        user_addr,
    )

    # manualy filter predictions for latter check Predictions
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))
    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp / 1000)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp / 1000)
    )

    # data frame after filtering is same as manual filtered dataframe
    pl.DataFrame.equals(mock_get_predictoor_summary_stats.call_args, preds_df)

    # number of rows from data frames are the same
    assert (
        mock_get_predictoor_summary_stats.call_args[0][0][0].shape[0]
        == preds_df.shape[0]
    )

    # the data frame was filtered by user address
    assert mock_get_predictoor_summary_stats.call_args[0][0][0]["user"][0] == user_addr

    assert mock_get_gql_dfs.call_count == 1
    assert mock_get_predictoor_summary_stats.call_count == 1


@enforce_types
@patch("pdr_backend.analytics.get_predictoors_info.get_predictoor_summary_stats")
@patch("pdr_backend.analytics.get_predictoors_info.GQLDataFactory.get_gql_dfs")
def test_get_predictoors_info_bad_date_range(
    mock_get_gql_dfs,
    mock_get_predictoor_summary_stats,
    _sample_first_predictions,
    tmpdir,
):
    st_timestr = "2023-12-20"
    fin_timestr = "2023-12-30"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _object_list_to_df(_sample_first_predictions, predictions_schema)
    mock_get_gql_dfs.return_value = {"pdr_predictions": predictions_df}

    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"

    # wrong date filter will lead to an assert
    with pytest.raises(AssertionError):
        get_predictoors_info_main(
            ppss,
            user_addr,
        )

    # Show filter leading to an empty dataframe
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))

    assert len(predictions_df) == 2

    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp / 1000)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp / 1000)
    )

    assert len(preds_df) == 0

    # show that summary_stats was never called
    assert mock_get_gql_dfs.call_count == 1
    assert mock_get_predictoor_summary_stats.call_count == 0


@enforce_types
@patch(
    "pdr_backend.analytics.get_predictoors_info.get_predictoor_summary_stats",
)
@patch("pdr_backend.analytics.get_predictoors_info.GQLDataFactory.get_gql_dfs")
def test_get_predictoors_info_bad_user_address(
    mock_get_gql_dfs,
    mock_get_predictoor_summary_stats,
    _sample_first_predictions,
    tmpdir,
):
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _object_list_to_df(_sample_first_predictions, predictions_schema)
    mock_get_gql_dfs.return_value = {"pdr_predictions": predictions_df}

    user_addr = "0xbbbb4cb4ff2584bad80ff5f109034a891c3d223"

    # Unknown user that leads to no records, will lead to an assert
    with pytest.raises(AssertionError):
        get_predictoors_info_main(
            ppss,
            user_addr,
        )

    # Show filter leading to an empty dataframe
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))
    assert len(predictions_df) == 0

    # show that summary_stats was never called
    assert mock_get_gql_dfs.call_count == 1
    assert mock_get_predictoor_summary_stats.call_count == 0
