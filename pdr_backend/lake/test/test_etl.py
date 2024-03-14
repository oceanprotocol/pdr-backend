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
from pdr_backend.lake.test.conftest import _clean_up_persistent_data_store
from pdr_backend.lake.table_registry import TableRegistry
from pdr_backend.lake.test.resources import _clean_up_table_registry
from pdr_backend.lake.persistent_data_store import PersistentDataStore

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


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_setup_etl(
    mock_get_gql_tables,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    _get_test_PDS,
    tmpdir,
):
    _clean_up_persistent_data_store(tmpdir)
    _clean_up_table_registry()

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

    gql_tables["pdr_predictions"].append_to_storage(preds)
    gql_tables["pdr_truevals"].append_to_storage(truevals)
    gql_tables["pdr_payouts"].append_to_storage(payouts)

    mock_get_gql_tables.return_value = gql_tables

    assert ppss.lake_ss.st_timestamp == UnixTimeMs.from_timestr(st_timestr)
    assert ppss.lake_ss.fin_timestamp == UnixTimeMs.from_timestr(fin_timestr)

    # Work 1: Initialize ETL - Assert 0 gql_dfs
    etl = ETL(ppss, gql_data_factory)

    assert etl is not None
    assert etl.gql_data_factory == gql_data_factory

    pds_instance = _get_test_PDS(tmpdir)

    # Assert original gql has 6 predictions, but we only got 5 due to date
    pdr_predictions_df = pds_instance.query_data("SELECT * FROM pdr_predictions")
    assert len(pdr_predictions_df) == 5
    assert len(_gql_datafactory_etl_predictions_df) == 6

    # Assert all 3 dfs are not the same because we filtered Nov 01 out
    pdr_payouts_df = pds_instance.query_data("SELECT * FROM pdr_payouts")
    assert len(pdr_payouts_df) != len(_gql_datafactory_etl_payouts_df)
    assert len(pdr_predictions_df) != len(_gql_datafactory_etl_predictions_df)

    pdr_truevals_df = pds_instance.query_data("SELECT * FROM pdr_truevals")

    assert len(pdr_truevals_df) != len(_gql_datafactory_etl_truevals_df)

    # Assert len of all 3 dfs
    assert len(pdr_payouts_df) == 4
    assert len(pdr_predictions_df) == 5
    assert len(pdr_truevals_df) == 5
    assert len(TableRegistry().get_tables()) == 5


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_tables")
def test_etl_do_bronze_step(
    mock_get_gql_tables,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    _get_test_PDS,
    tmpdir,
):
    _clean_up_persistent_data_store(tmpdir)
    _clean_up_table_registry()

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

    gql_tables = {
        "pdr_predictions": Table(predictions_table_name, predictions_schema, ppss),
        "pdr_truevals": Table(truevals_table_name, truevals_schema, ppss),
        "pdr_payouts": Table(payouts_table_name, payouts_schema, ppss),
    }

    gql_tables["pdr_predictions"].append_to_storage(preds, True)
    gql_tables["pdr_truevals"].append_to_storage(truevals, True)
    gql_tables["pdr_payouts"].append_to_storage(payouts, True)

    mock_get_gql_tables.return_value = gql_tables

    # Work 1: Initialize ETL
    etl = ETL(ppss, gql_data_factory)

    pds_instance = _get_test_PDS(tmpdir)
    pdr_predictions_records = pds_instance.query_data(
        f"""
            SELECT * FROM _build_{predictions_table_name}
        """
    )
    assert len(pdr_predictions_records) == 6

    # Work 3: Do bronze
    etl.do_bronze_step()

    # assert bronze_pdr_predictions_df is created
    bronze_pdr_predictions_records = pds_instance.query_data(
        "SELECT * FROM _build_bronze_pdr_predictions"
    )
    assert len(bronze_pdr_predictions_records) == 6

    # bronze_pdr_predictions_df = etl.tables["bronze_pdr_predictions"].df
    bronze_pdr_predictions_df = bronze_pdr_predictions_records

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
        == _gql_datafactory_etl_truevals_df["truevalue"][1]
    )
    assert (
        bronze_pdr_predictions_df["truevalue"][2]
        == _gql_datafactory_etl_truevals_df["truevalue"][2]
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

@enforce_types
def test_check_build_sql_tables(
    tmpdir
):
    etl = ETL(None, None)
    pds = PersistentDataStore(str(tmpdir))

    db_tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    #SELECT ALL TABLES FROM DB 
    db_tables = pds.duckdb_conn.execute(
        db_tables_query
    ).fetchall()

    # DROP ALL TABLES
    for table in db_tables:
        pds.duckdb_conn.execute(f"DROP TABLE {table[0]}")

    pds.create_table(pl.DataFrame(), "_build_a")
    pds.create_table(pl.DataFrame(), "_build_b")
    pds.create_table(pl.DataFrame(), "_build_c")

    #check if tables are created
    db_tables = pds.duckdb_conn.execute(
        db_tables_query
    ).fetchall()

    assert len(db_tables) == 3

    etl.build_table_names = ["a", "b", "c"]
    etl._check_build_sql_tables()

    db_tables = pds.duckdb_conn.execute(
        db_tables_query
    ).fetchall()

    assert len(db_tables) == 0

@enforce_types
def test_move_build_tables_to_permanent(
    tmpdir
):
    etl = ETL(None, None)
    pds = PersistentDataStore(str(tmpdir))

    db_tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    #SELECT ALL TABLES FROM DB 
    db_tables = pds.duckdb_conn.execute(
        db_tables_query
    ).fetchall()

    # DROP ALL TABLES
    for table in db_tables:
        pds.duckdb_conn.execute(f"DROP TABLE {table[0]}")

    pds.create_table(pl.DataFrame(), "_build_a")
    pds.create_table(pl.DataFrame(), "_build_b")
    pds.create_table(pl.DataFrame(), "_build_c")

    #check if tables are created
    db_tables = pds.duckdb_conn.execute(
        db_tables_query
    ).fetchall()

    assert len(db_tables) == 3

    etl.build_table_names = ["a", "b", "c"]
    etl._move_build_tables_to_permanent()

    db_tables = pds.duckdb_conn.execute(
        db_tables_query
    ).fetchall()

    assert len(db_tables) == 3
    assert db_tables[0][0] == "a"
    assert db_tables[1][0] == "b"
    assert db_tables[2][0] == "c"
