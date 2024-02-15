from unittest.mock import patch
import pytest
from enforce_typing import enforce_types
import polars as pl
from pdr_backend.lake.table import Table
from pdr_backend.analytics.get_predictions_info import get_predictions_info_main
from pdr_backend.ppss.ppss import mock_ppss

table_name = "pdr_predictions"


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.get_feed_summary_stats")
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_get_predictions_info_main_mainnet(
    mock_get_gql_tables,
    mock_get_feed_summary_stats,
    _gql_datafactory_first_predictions_df,
    tmpdir,
):
    """
    @description
        assert everything works as expected under normal conditions
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )
    predictions_df = _gql_datafactory_first_predictions_df
    predictions_table = Table(table_name, predictions_df.schema, ppss)
    predictions_table.df = predictions_df
    mock_get_gql_tables.return_value = {"pdr_predictions": predictions_table}

    feed_addr = "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152"
    get_predictions_info_main(
        ppss,
        st_timestr,
        fin_timestr,
        [feed_addr],
    )

    # manualy filter predictions for latter check Predictions
    predictions_df = predictions_df.filter(
        predictions_df["ID"].map_elements(lambda x: x.split("-")[0]).is_in([feed_addr])
    )

    assert len(predictions_df) == 1

    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp)
    )

    assert len(preds_df) == 1

    # number of rows from data frames are the same
    assert mock_get_feed_summary_stats.call_args[0][0][0].shape[0] == preds_df.shape[0]

    # the data frame was filtered by feed address
    assert (
        mock_get_feed_summary_stats.call_args[0][0][0]["ID"][0].split("-")[0]
        == feed_addr
    )

    # data frame after filtering is same as manual filtered dataframe
    pl.DataFrame.equals(mock_get_feed_summary_stats.call_args, preds_df)

    assert mock_get_gql_tables.call_count == 1
    assert mock_get_feed_summary_stats.call_count == 1


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.get_feed_summary_stats")
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_get_predictions_info_bad_date_range(
    mock_get_gql_tables,
    get_feed_summary_stats,
    _gql_datafactory_first_predictions_df,
    tmpdir,
):
    """
    @description
        assert date range filter asserts it has records before calculating stats
    """
    st_timestr = "2023-12-20"
    fin_timestr = "2023-12-21"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _gql_datafactory_first_predictions_df
    mock_get_gql_tables.return_value = {
        "pdr_predictions": Table(table_name, predictions_df.schema, ppss)
    }

    feed_addr = "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152"

    # wrong feed address will raise error, lets wrap the call for test
    with pytest.raises(AssertionError):
        get_predictions_info_main(
            ppss,
            st_timestr,
            fin_timestr,
            [feed_addr],
        )

    # Work 1: Internal filter returns 0 rows due to date mismatch
    predictions_df = predictions_df.filter(
        predictions_df["ID"].map_elements(lambda x: x.split("-")[0]).is_in([feed_addr])
    )

    assert len(predictions_df) == 1

    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp)
    )

    assert len(preds_df) == 0

    assert mock_get_gql_tables.call_count == 1
    assert get_feed_summary_stats.call_count == 0


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.get_feed_summary_stats")
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_get_predictions_info_bad_feed(
    mock_get_gql_tables,
    mock_get_feed_summary_stats,
    _gql_datafactory_first_predictions_df,
    tmpdir,
):
    """
    @description
        assert feeds filter ends up with records before calculating stats
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _gql_datafactory_first_predictions_df
    mock_get_gql_tables.return_value = {
        "pdr_predictions": Table(table_name, predictions_df.schema, ppss)
    }

    feed_addr = "0x8e0we267779d27c2b3ed5408408ff15d9f3a3152"

    # wrong feed address will raise error because there will be no data to process
    with pytest.raises(AssertionError):
        get_predictions_info_main(
            ppss,
            st_timestr,
            fin_timestr,
            [feed_addr],
        )

    # show that feed address can't be found
    predictions_df = predictions_df.filter(
        predictions_df["ID"].map_elements(lambda x: x.split("-")[0]).is_in([feed_addr])
    )

    assert len(predictions_df) == 0

    assert mock_get_gql_tables.call_count == 1
    assert mock_get_feed_summary_stats.call_count == 0


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_get_predictions_info_empty(mock_get_gql_tables, tmpdir):
    """
    @description
        assert data factory returns valid records before calculating stats
    """
    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    # mockt he gql data factory not having any records
    mock_get_gql_tables.return_value = {"pdr_predictions": Table(table_name, {}, ppss)}

    feed_addr = "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152"

    # gql_data_factory returning empty dataframe will raise error
    with pytest.raises(AssertionError):
        get_predictions_info_main(
            ppss,
            st_timestr,
            fin_timestr,
            [feed_addr],
        )
