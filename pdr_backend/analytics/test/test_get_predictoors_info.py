from unittest.mock import patch

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.table_pdr_predictions import (
    _object_list_to_df,
    predictions_schema,
)
from pdr_backend.analytics.get_predictoors_info import get_predictoors_info_main
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.util.timeutil import timestr_to_ut


@enforce_types
@patch(
    "pdr_backend.analytics.get_predictoors_info.get_predictoor_summary_stats",
    spec=pl.DataFrame,
)
@patch("pdr_backend.analytics.get_predictoors_info.GQLDataFactory.get_gql_dfs")
def test_get_predictoors_info_main_mainnet(
    mock_getPolars, mock_getstats, _sample_first_predictions, tmpdir
):
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    predictions_df = _object_list_to_df(_sample_first_predictions, predictions_schema)
    mock_getPolars.return_value = {"pdr_predictions": predictions_df}

    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    get_predictoors_info_main(
        ppss,
        st_timestr,
        fin_timestr,
        user_addr,
    )

    # manualy filter predictions for latter check Predictions
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))
    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= timestr_to_ut(st_timestr) / 1000)
        & (predictions_df["timestamp"] <= timestr_to_ut(fin_timestr) / 1000)
    )

    # data frame after filtering is same as manual filtered dataframe
    pl.DataFrame.equals(mock_getstats.call_args, preds_df)

    # number of rows from data frames are the same
    assert mock_getstats.call_args[0][0][0].shape[0] == preds_df.shape[0]

    # the data frame was filtered by user address
    assert mock_getstats.call_args[0][0][0]["user"][0] == user_addr

    assert mock_getPolars.call_count == 1
    assert mock_getstats.call_count == 1


@enforce_types
@patch(
    "pdr_backend.analytics.get_predictoors_info.get_predictoor_summary_stats",
    spec=pl.DataFrame,
)
@patch("pdr_backend.analytics.get_predictoors_info.GQLDataFactory.get_gql_dfs")
def test_empty_data_frame_timeframe_filter_mainnet(
    mock_getPolars, mock_getstats, _sample_first_predictions, tmpdir
):
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    predictions_df = _object_list_to_df(_sample_first_predictions, predictions_schema)
    mock_getPolars.return_value = {"pdr_predictions": predictions_df}

    st_timestr = "2023-12-20"
    fin_timestr = "2023-12-30"
    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    get_predictoors_info_main(
        ppss,
        st_timestr,
        fin_timestr,
        user_addr,
    )

    # manualy filter predictions for latter check Predictions
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))
    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= timestr_to_ut(st_timestr) / 1000)
        & (predictions_df["timestamp"] <= timestr_to_ut(fin_timestr) / 1000)
    )

    # data frame after filtering is same as manual filtered dataframe
    pl.DataFrame.equals(mock_getstats.call_args, preds_df)

    # number of rows from data frames are the same
    assert mock_getstats.call_args[0][0][0].shape[0] == preds_df.shape[0]

    # the data frame is empy
    assert mock_getstats.call_args[0][0][0].shape[0] == 0

    assert mock_getPolars.call_count == 1
    assert mock_getstats.call_count == 1


@enforce_types
@patch(
    "pdr_backend.analytics.get_predictoors_info.get_predictoor_summary_stats",
    spec=pl.DataFrame,
)
@patch("pdr_backend.analytics.get_predictoors_info.GQLDataFactory.get_gql_dfs")
def test_empty_data_frame_user_address_filter_mainnet(
    mock_getPolars, mock_getstats, _sample_first_predictions, tmpdir
):
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    predictions_df = _object_list_to_df(_sample_first_predictions, predictions_schema)
    mock_getPolars.return_value = {"pdr_predictions": predictions_df}

    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    user_addr = "0xbbbb4cb4ff2584bad80ff5f109034a891c3d223"
    get_predictoors_info_main(
        ppss,
        st_timestr,
        fin_timestr,
        user_addr,
    )

    # manualy filter predictions for latter check Predictions
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))
    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= timestr_to_ut(st_timestr) / 1000)
        & (predictions_df["timestamp"] <= timestr_to_ut(fin_timestr) / 1000)
    )

    # data frame after filtering is same as manual filtered dataframe
    pl.DataFrame.equals(mock_getstats.call_args, preds_df)

    # number of rows from data frames are the same
    assert mock_getstats.call_args[0][0][0].shape[0] == preds_df.shape[0]

    # the data frame is empy
    assert mock_getstats.call_args[0][0][0].shape[0] == 0

    assert mock_getPolars.call_count == 1
    assert mock_getstats.call_count == 1
