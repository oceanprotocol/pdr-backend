from unittest.mock import patch
from enforce_typing import enforce_types

import polars as pl
from pdr_backend.util.timeutil import timestr_to_ut
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.etl import ETL

# ETL code-coverage
# Step 1. ETL -> do_sync_step()
# Step 2. ETL -> do_bronze_step()


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_dfs")
def test_setup_etl(
    mock_get_gql_dfs,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    tmpdir,
):
    # setup test start-end date
    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    # Mock dfs based on configured st/fin timestamps
    preds = _gql_datafactory_etl_predictions_df.filter(
        (pl.col("timestamp") >= timestr_to_ut(st_timestr)) &
        (pl.col("timestamp") <= timestr_to_ut(fin_timestr))
    )
    truevals = _gql_datafactory_etl_truevals_df.filter(
        (pl.col("timestamp") >= timestr_to_ut(st_timestr)) &
        (pl.col("timestamp") <= timestr_to_ut(fin_timestr))
    )
    payouts = _gql_datafactory_etl_payouts_df.filter(
        (pl.col("timestamp") >= timestr_to_ut(st_timestr)) &
        (pl.col("timestamp") <= timestr_to_ut(fin_timestr))
    )

    gql_dfs = {
        "pdr_predictions": preds,
        "pdr_truevals": truevals,
        "pdr_payouts": payouts,
    }
    mock_get_gql_dfs.return_value = gql_dfs
    
    # Setup PPSS + Data Factory
    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    assert ppss.lake_ss.st_timestamp == timestr_to_ut(st_timestr)
    assert ppss.lake_ss.fin_timestamp == timestr_to_ut(fin_timestr)

    # Work 1: Initialize ETL - Assert 0 gql_dfs
    etl = ETL(ppss, gql_data_factory)

    assert etl is not None
    assert etl.gql_data_factory == gql_data_factory
    assert len(etl.dfs) == 0

    # Work 2: Complete ETL sync step - Assert 3 gql_dfs
    etl.do_sync_step()

    # Assert original gql has 6 predictions, but we only got 5 due to date
    assert len(etl.dfs) == 3
    assert len(etl.dfs["pdr_predictions"]) == 5
    assert len(_gql_datafactory_etl_predictions_df) == 6

    # Assert all 3 dfs are not the same because we filtered Nov 01 out
    assert len(etl.dfs["pdr_payouts"]) != len(_gql_datafactory_etl_payouts_df)
    assert len(etl.dfs["pdr_predictions"]) != len(_gql_datafactory_etl_predictions_df)
    assert len(etl.dfs["pdr_truevals"]) != len(_gql_datafactory_etl_truevals_df)

    # Assert len of all 3 dfs
    assert len(etl.dfs["pdr_payouts"]) == 4
    assert len(etl.dfs["pdr_predictions"]) == 5
    assert len(etl.dfs["pdr_truevals"]) == 5


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_dfs")
def test_etl_do_bronze_step(
    mock_get_gql_dfs,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    tmpdir,
):
    # please note date, including Nov 1st
    st_timestr = "2023-11-01_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    preds = _gql_datafactory_etl_predictions_df.filter(
        (pl.col("timestamp") >= timestr_to_ut(st_timestr)) &
        (pl.col("timestamp") <= timestr_to_ut(fin_timestr))
    )
    truevals = _gql_datafactory_etl_truevals_df.filter(
        (pl.col("timestamp") >= timestr_to_ut(st_timestr)) &
        (pl.col("timestamp") <= timestr_to_ut(fin_timestr))
    )
    payouts = _gql_datafactory_etl_payouts_df.filter(
        (pl.col("timestamp") >= timestr_to_ut(st_timestr)) &
        (pl.col("timestamp") <= timestr_to_ut(fin_timestr))
    )

    # Work 2: Complete ETL sync step - Assert 3 gql_dfs
    gql_dfs = {
        "pdr_predictions": preds,
        "pdr_truevals": truevals,
        "pdr_payouts": payouts,
    }
    
    mock_get_gql_dfs.return_value = gql_dfs

    # Work 1: Initialize ETL
    etl = ETL(ppss, gql_data_factory)

    # Work 2: Do sync
    etl.do_sync_step()

    assert len(etl.dfs["pdr_predictions"]) == 6

    # Work 3: Do bronze
    etl.do_bronze_step()

    # assert bronze_pdr_predictions_df is created
    assert len(etl.dfs["bronze_pdr_predictions"]) == 6

    bronze_pdr_predictions_df = etl.dfs["bronze_pdr_predictions"]

    # Assert that "contract" data was created, and matches the same data from pdr_predictions
    assert (
        bronze_pdr_predictions_df["contract"][0]
        == "0x30f1c55e72fe105e4a1fbecdff3145fc14177695"
    )
    assert (
        bronze_pdr_predictions_df["contract"][1]
        == _gql_datafactory_etl_predictions_df["contract"][1]
    )
    assert (
        bronze_pdr_predictions_df["contract"][2]
        == _gql_datafactory_etl_predictions_df["contract"][2]
    )

    # Assert timestamp == predictions timestamp
    assert (
        bronze_pdr_predictions_df["timestamp"][1]
        == _gql_datafactory_etl_predictions_df["timestamp"][1]
    )
    assert (
        bronze_pdr_predictions_df["timestamp"][2]
        == _gql_datafactory_etl_predictions_df["timestamp"][2]
    )

    # Assert last_event_timestamp == payout.timestamp
    assert (
        bronze_pdr_predictions_df["last_event_timestamp"][1]
        == _gql_datafactory_etl_payouts_df["timestamp"][1]
    )
    assert (
        bronze_pdr_predictions_df["last_event_timestamp"][2]
        == _gql_datafactory_etl_payouts_df["timestamp"][2]
    )

    # Assert predictions.truevalue == gql truevals_df
    assert bronze_pdr_predictions_df["truevalue"][1] == True
    assert bronze_pdr_predictions_df["truevalue"][2] == False

    assert (
        bronze_pdr_predictions_df["truevalue"][1]
        == _gql_datafactory_etl_truevals_df["trueval"][1]
    )
    assert (
        bronze_pdr_predictions_df["truevalue"][2]
        == _gql_datafactory_etl_truevals_df["trueval"][2]
    )

    # Assert payout ts > prediction ts
    assert (
        bronze_pdr_predictions_df["last_event_timestamp"][0]
        > bronze_pdr_predictions_df["timestamp"][0]
    )
    assert (
        bronze_pdr_predictions_df["last_event_timestamp"][1]
        > bronze_pdr_predictions_df["timestamp"][1]
    )

    # Assert payout came from payouts
    assert round(bronze_pdr_predictions_df["payout"][1], 3) == round(
        _gql_datafactory_etl_payouts_df["payout"][1], 3
    )
    assert round(bronze_pdr_predictions_df["payout"][2], 3) == round(
        _gql_datafactory_etl_payouts_df["payout"][2], 3
    )

    # Assert stake in the bronze_table came from payouts
    assert round(bronze_pdr_predictions_df["stake"][1], 3) == round(
        _gql_datafactory_etl_payouts_df["stake"][1], 3
    )
    assert round(bronze_pdr_predictions_df["stake"][2], 3) == round(
        _gql_datafactory_etl_payouts_df["stake"][2], 3
    )
