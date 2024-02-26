from unittest.mock import patch
from enforce_typing import enforce_types

import polars as pl
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.etl import ETL
from pdr_backend.lake.table import Table
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
    predictions_table_name,
)
from pdr_backend.lake.table_pdr_truevals import truevals_schema, truevals_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_schema, payouts_table_name
from pdr_backend.lake.table_pdr_slots import slots_schema, slots_table_name

# ETL code-coverage
# Step 1. ETL -> do_sync_step()
# Step 2. ETL -> do_bronze_step()


@enforce_types
def get_filtered_timestamps_df(
    df: pl.DataFrame, st_timestr: str, fin_timestr: str
) -> pl.DataFrame:
    return df.filter(
        (pl.col("timestamp") >= UnixTimeMs.from_timestr(st_timestr))
        & (pl.col("timestamp") <= UnixTimeMs.from_timestr(fin_timestr))
    )


# pylint: disable=too-many-statements
@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_setup_etl(
    mock_get_gql_tables,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    tmpdir,
):
    # setup test start-end date
    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    # Mock dfs based on configured st/fin timestamps
    preds = get_filtered_timestamps_df(
        _gql_datafactory_etl_predictions_df, st_timestr, fin_timestr
    )
    truevals = get_filtered_timestamps_df(
        _gql_datafactory_etl_truevals_df, st_timestr, fin_timestr
    )
    payouts = get_filtered_timestamps_df(
        _gql_datafactory_etl_payouts_df, st_timestr, fin_timestr
    )

    # Setup PPSS + Data Factory
    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    gql_tables = {
        "pdr_predictions": Table(predictions_table_name, predictions_schema, ppss),
        "pdr_truevals": Table(truevals_table_name, truevals_schema, ppss),
        "pdr_payouts": Table(payouts_table_name, payouts_schema, ppss),
    }

    gql_tables["pdr_predictions"].df = preds
    gql_tables["pdr_truevals"].df = truevals
    gql_tables["pdr_payouts"].df = payouts

    mock_get_gql_tables.return_value = gql_tables

    assert ppss.lake_ss.st_timestamp == UnixTimeMs.from_timestr(st_timestr)
    assert ppss.lake_ss.fin_timestamp == UnixTimeMs.from_timestr(fin_timestr)

    # Work 1: Initialize ETL - Assert 0 etl_tables
    etl = ETL(ppss, gql_data_factory)

    assert etl is not None
    assert etl.gql_data_factory == gql_data_factory
    assert len(etl.tables) == 0

    # Work 2: Complete ETL sync step - Assert 3 etl_tables
    etl.do_sync_step()

    # Assert original gql has 6 predictions, but we only got 5 due to date
    assert len(etl.tables) == 3
    assert len(etl.tables["pdr_predictions"].df) == 5
    assert len(_gql_datafactory_etl_predictions_df) == 6

    # Assert all 3 dfs are not the same because we filtered Nov 01 out
    assert len(etl.tables["pdr_payouts"].df) != len(_gql_datafactory_etl_payouts_df)
    assert len(etl.tables["pdr_predictions"].df) != len(
        _gql_datafactory_etl_predictions_df
    )
    assert len(etl.tables["pdr_truevals"].df) != len(_gql_datafactory_etl_truevals_df)

    # Assert len of all 3 dfs
    assert len(etl.tables["pdr_payouts"].df) == 4
    assert len(etl.tables["pdr_predictions"].df) == 5
    assert len(etl.tables["pdr_truevals"].df) == 5


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_etl_do_bronze_step(
    mock_get_gql_tables,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    _gql_datafactory_etl_slots_df,
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

    preds = get_filtered_timestamps_df(
        _gql_datafactory_etl_predictions_df, st_timestr, fin_timestr
    )
    truevals = get_filtered_timestamps_df(
        _gql_datafactory_etl_truevals_df, st_timestr, fin_timestr
    )
    payouts = get_filtered_timestamps_df(
        _gql_datafactory_etl_payouts_df, st_timestr, fin_timestr
    )
    slots = get_filtered_timestamps_df(
        _gql_datafactory_etl_slots_df, st_timestr, fin_timestr
    )

    # Work 2: Complete ETL sync step - Assert 4 gql_tables
    gql_tables = {
        "pdr_predictions": Table(predictions_table_name, predictions_schema, ppss),
        "pdr_truevals": Table(truevals_table_name, truevals_schema, ppss),
        "pdr_payouts": Table(payouts_table_name, payouts_schema, ppss),
        "pdr_slots": Table(slots_table_name, slots_schema, ppss),
    }

    gql_tables["pdr_predictions"].df = preds
    gql_tables["pdr_truevals"].df = truevals
    gql_tables["pdr_payouts"].df = payouts
    gql_tables["pdr_slots"].df = slots

    mock_get_gql_tables.return_value = gql_tables

    # Work 1: Initialize ETL
    etl = ETL(ppss, gql_data_factory)

    # Work 2: Do sync
    etl.do_sync_step()

    assert len(etl.tables["pdr_predictions"].df) == 6

    # Work 3: Do bronze
    etl.do_bronze_step()

    # assert bronze_pdr_predictions_df is created
    assert len(etl.tables["bronze_pdr_predictions"].df) == 6

    bronze_pdr_predictions_df = etl.tables["bronze_pdr_predictions"].df

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
    assert bronze_pdr_predictions_df["truevalue"][1] is True
    assert bronze_pdr_predictions_df["truevalue"][2] is False

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

    # assert bronze_pdr_slots_df is created
    assert len(etl.tables["bronze_pdr_slots"].df) == 7

    bronze_pdr_slots_df = etl.tables["bronze_pdr_slots"].df

    # Assert that "contract" data was created, and matches the same data from pdr_predictions
    assert (
        bronze_pdr_slots_df["contract"][0]
        == "0x30f1c55e72fe105e4a1fbecdff3145fc14177695"
    )
    assert (
        bronze_pdr_slots_df["contract"][1]
        == _gql_datafactory_etl_predictions_df["contract"][1]
    )
    assert (
        bronze_pdr_slots_df["contract"][2]
        == _gql_datafactory_etl_predictions_df["contract"][2]
    )

    # Assert timestamp == slots timestamp
    assert (
        bronze_pdr_slots_df["timestamp"][1]
        == _gql_datafactory_etl_slots_df["timestamp"][1]
    )
    assert (
        bronze_pdr_slots_df["timestamp"][2]
        == _gql_datafactory_etl_slots_df["timestamp"][2]
    )

    # Assert last_event_timestamp == prediction.timestamp
    assert (
        bronze_pdr_slots_df["last_event_timestamp"][1]
        == _gql_datafactory_etl_predictions_df["timestamp"][1]
    )
    assert (
        bronze_pdr_slots_df["last_event_timestamp"][2]
        == _gql_datafactory_etl_predictions_df["timestamp"][2]
    )

    # Assert predictions.truevalue == gql truevals_df
    assert bronze_pdr_slots_df["trueval"][1] is True
    assert bronze_pdr_slots_df["trueval"][2] is False

    assert (
        bronze_pdr_slots_df["trueval"][1]
        == _gql_datafactory_etl_truevals_df["trueval"][1]
    )
    assert (
        bronze_pdr_slots_df["trueval"][2]
        == _gql_datafactory_etl_truevals_df["trueval"][2]
    )

    # Assert stake in the bronze_table came from slots
    try:
        assert round(bronze_pdr_slots_df["roundSumStakes"][1], 3) == round(
            _gql_datafactory_etl_slots_df["roundSumStakes"][1], 3
        )
        assert round(bronze_pdr_slots_df["roundSumStakes"][2], 3) == round(
            _gql_datafactory_etl_slots_df["roundSumStakes"][2], 3
        )
    except TypeError as e:
        assert str(e) == "type NoneType doesn't define __round__ method"
