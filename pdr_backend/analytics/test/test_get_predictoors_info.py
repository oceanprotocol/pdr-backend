from unittest.mock import patch
import pytest

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.legacy.table import Table
from pdr_backend.analytics.get_predictions_info import get_predictoors_info_main
from pdr_backend.ppss.ppss import mock_ppss

table_name = "pdr_predictoors"


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.get_predictoor_summary_stats")
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_get_predictoors_info_main_mainnet(
    mock_get_gql_tables,
    mock_get_predictoor_summary_stats,
    _gql_datafactory_first_predictions_df,
    tmpdir,
):
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _gql_datafactory_first_predictions_df
    predictions_table = Table(table_name, predictions_df.schema, ppss)
    predictions_table.df = predictions_df
    mock_get_gql_tables.return_value = {"pdr_predictions": predictions_table}

    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"

    get_predictoors_info_main(
        ppss,
        st_timestr,
        fin_timestr,
        [user_addr],
    )

    # manualy filter predictions for latter check Predictions
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))
    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp)
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

    assert mock_get_gql_tables.call_count == 1
    assert mock_get_predictoor_summary_stats.call_count == 1


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.get_predictoor_summary_stats")
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_get_predictoors_info_bad_date_range(
    mock_get_gql_tables,
    mock_get_predictoor_summary_stats,
    _gql_datafactory_first_predictions_df,
    tmpdir,
):
    st_timestr = "2023-12-20"
    fin_timestr = "2023-12-30"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _gql_datafactory_first_predictions_df
    mock_get_gql_tables.return_value = {
        "pdr_predictions": Table(table_name, predictions_df.schema, ppss)
    }

    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"

    # wrong date filter will lead to an assert
    with pytest.raises(AssertionError):
        get_predictoors_info_main(
            ppss,
            st_timestr,
            fin_timestr,
            [user_addr],
        )

    # Show filter leading to an empty dataframe
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))

    assert len(predictions_df) == 2

    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp)
    )

    assert len(preds_df) == 0

    # show that summary_stats was never called
    assert mock_get_gql_tables.call_count == 1
    assert mock_get_predictoor_summary_stats.call_count == 0


@enforce_types
@patch(
    "pdr_backend.analytics.predictoor_stats.get_predictoor_summary_stats",
)
@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory.get_gql_tables")
def test_get_predictoors_info_bad_user_address(
    mock_get_gql_tables,
    mock_get_predictoor_summary_stats,
    _gql_datafactory_first_predictions_df,
    tmpdir,
):
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _gql_datafactory_first_predictions_df
    mock_get_gql_tables.return_value = {
        "pdr_predictions": Table(table_name, predictions_df.schema, ppss)
    }

    user_addr = "0xbbbb4cb4ff2584bad80ff5f109034a891c3d223"

    # Unknown user that leads to no records, will lead to an assert
    with pytest.raises(AssertionError):
        get_predictoors_info_main(
            ppss,
            st_timestr,
            fin_timestr,
            [user_addr],
        )

    # Show filter leading to an empty dataframe
    predictions_df = predictions_df.filter(predictions_df["user"].is_in([user_addr]))
    assert len(predictions_df) == 0

    # show that summary_stats was never called
    assert mock_get_gql_tables.call_count == 1
    assert mock_get_predictoor_summary_stats.call_count == 0
