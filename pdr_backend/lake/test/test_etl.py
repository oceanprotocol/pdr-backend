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
from pdr_backend.lake.plutil import get_table_name, TableType


@enforce_types
def get_filtered_timestamps_df(
    df: pl.DataFrame, st_timestr: str, fin_timestr: str
) -> pl.DataFrame:
    return df.filter(
        (pl.col("timestamp") >= UnixTimeMs.from_timestr(st_timestr))
        & (pl.col("timestamp") <= UnixTimeMs.from_timestr(fin_timestr))
    )


@enforce_types
def test_setup_etl(
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

    assert ppss.lake_ss.st_timestamp == UnixTimeMs.from_timestr(st_timestr)
    assert ppss.lake_ss.fin_timestamp == UnixTimeMs.from_timestr(fin_timestr)

    # Work 1: Initialize ETL - Assert 0 gql_dfs
    etl = ETL(ppss, gql_data_factory)

    assert etl is not None
    assert etl.gql_data_factory == gql_data_factory

    pds = _get_test_PDS(tmpdir)

    # Assert original gql has 6 predictions, but we only got 5 due to date
    pdr_predictions_df = pds.query_data("SELECT * FROM pdr_predictions")
    assert len(pdr_predictions_df) == 5
    assert len(_gql_datafactory_etl_predictions_df) == 6

    # Assert all 3 dfs are not the same because we filtered Nov 01 out
    pdr_payouts_df = pds.query_data("SELECT * FROM pdr_payouts")
    assert len(pdr_payouts_df) != len(_gql_datafactory_etl_payouts_df)
    assert len(pdr_predictions_df) != len(_gql_datafactory_etl_predictions_df)

    pdr_truevals_df = pds.query_data("SELECT * FROM pdr_truevals")

    assert len(pdr_truevals_df) != len(_gql_datafactory_etl_truevals_df)

    # Assert len of all 3 dfs
    assert len(pdr_payouts_df) == 4
    assert len(pdr_predictions_df) == 5
    assert len(pdr_truevals_df) == 5
    assert len(TableRegistry().get_tables()) == 5


@enforce_types
def test_etl_do_bronze_step(
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

    gql_tables["pdr_predictions"].append_to_storage(preds, TableType.TEMP)
    gql_tables["pdr_truevals"].append_to_storage(truevals, TableType.TEMP)
    gql_tables["pdr_payouts"].append_to_storage(payouts, TableType.TEMP)

    # Work 1: Initialize ETL
    etl = ETL(ppss, gql_data_factory)

    pds = _get_test_PDS(tmpdir)
    temp_table_name = get_table_name(predictions_table_name, TableType.TEMP)
    pdr_predictions_records = pds.query_data("SELECT * FROM {}".format(temp_table_name))
    assert len(pdr_predictions_records) == 6

    # Work 3: Do bronze
    etl.do_bronze_step()

    # assert bronze_pdr_predictions_df is created
    temp_table_name = get_table_name("bronze_pdr_predictions", TableType.TEMP)
    bronze_pdr_predictions_records = pds.query_data(
        "SELECT * FROM {}".format(temp_table_name)
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
def test_drop_temp_sql_tables(tmpdir):

    # setup test start-end date
    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    etl = ETL(ppss, gql_data_factory)
    pds = PersistentDataStore(str(tmpdir))

    # SELECT ALL TABLES FROM DB
    table_names = pds.get_table_names()

    # DROP ALL TABLES
    for table in table_names:
        pds.duckdb_conn.execute(f"DROP TABLE {table}")

    dummy_schema = {"test_column": str}
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_a")
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_b")
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_c")

    # check if tables are created
    table_names = pds.get_table_names()

    assert len(table_names) == 3

    etl.temp_table_names = ["a", "b", "c"]
    etl._drop_temp_sql_tables()

    table_names = pds.get_table_names()

    assert len(table_names) == 0


@enforce_types
def test_move_from_temp_tables_to_live(tmpdir):

    # setup test start-end date
    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    etl = ETL(ppss, gql_data_factory)
    pds = PersistentDataStore(str(tmpdir))

    # SELECT ALL TABLES FROM DB
    table_names = pds.get_table_names()

    # DROP ALL TABLES
    for table_name in table_names:
        pds.duckdb_conn.execute(f"DROP TABLE {table_name}")

    dummy_schema = {"test_column": str}
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_a")
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_b")
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_c")

    # check if tables are created
    table_names = pds.get_table_names()

    assert len(table_names) == 3

    etl.temp_table_names = ["a", "b", "c"]
    etl._move_from_temp_tables_to_live()

    table_names = pds.get_table_names()

    assert len(table_names) == 3
    # check "c" exists in permanent tables
    assert "c" in table_names
    assert "a" in table_names
    assert "b" in table_names

    # Verify no build tables exist
    table_names = pds.get_table_names()

    for table_name in table_names:
        assert "_temp_" not in table_name


@enforce_types
def test_get_max_timestamp_values_from(tmpdir):
    _clean_up_persistent_data_store(tmpdir)
    pds = PersistentDataStore(str(tmpdir))

    pds.duckdb_conn.execute(
        """
        CREATE TABLE test_table_1 (timestamp TIMESTAMP);
        CREATE TABLE test_table_2 (timestamp TIMESTAMP);
        CREATE TABLE test_table_3 (timestamp TIMESTAMP);
        """
    )

    pds.duckdb_conn.execute(
        """
        INSERT INTO test_table_1 VALUES ('2023-11-02 00:00:00');
        INSERT INTO test_table_2 VALUES ('2023-11-03 00:00:00');
        INSERT INTO test_table_2 VALUES ('2023-11-09 00:00:00');
        INSERT INTO test_table_3 VALUES ('2023-11-04 00:00:00');
        """
    )

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    etl = ETL(ppss, gql_data_factory)

    max_timestamp_values = etl._get_max_timestamp_values_from(
        ["test_table_1", "test_table_2", "test_table_3"]
    )

    assert (
        max_timestamp_values["test_table_1"].strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 00:00:00"
    )
    assert (
        max_timestamp_values["test_table_2"].strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-09 00:00:00"
    )
    assert (
        max_timestamp_values["test_table_3"].strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-04 00:00:00"
    )


@enforce_types
def test_calc_bronze_start_end_ts(tmpdir):
    _clean_up_persistent_data_store(tmpdir)
    pds = PersistentDataStore(str(tmpdir))

    pds.duckdb_conn.execute(
        """
        CREATE TABLE test_bronze_table_1 (timestamp TIMESTAMP);
        CREATE TABLE test_bronze_table_2 (timestamp TIMESTAMP);
        CREATE TABLE test_bronze_table_3 (timestamp TIMESTAMP);
        """
    )

    pds.duckdb_conn.execute(
        """
        CREATE TABLE _temp_dummy_table_1 (timestamp TIMESTAMP);
        CREATE TABLE _temp_dummy_table_2 (timestamp TIMESTAMP);
        CREATE TABLE _temp_dummy_table_3 (timestamp TIMESTAMP);
        """
    )

    pds.duckdb_conn.execute(
        """
        INSERT INTO test_bronze_table_1 VALUES ('2023-11-04 00:00:00');
        INSERT INTO test_bronze_table_2 VALUES ('2023-11-05 00:00:00');
        INSERT INTO test_bronze_table_2 VALUES ('2023-11-01 00:00:00');
        INSERT INTO test_bronze_table_3 VALUES ('2023-11-02 00:00:00');
        """
    )

    pds.duckdb_conn.execute(
        """
        INSERT INTO _temp_dummy_table_1 VALUES ('2023-11-21 00:00:00');
        INSERT INTO _temp_dummy_table_2 VALUES ('2023-11-23 00:00:00');
        INSERT INTO _temp_dummy_table_2 VALUES ('2023-11-22 00:00:00');
        INSERT INTO _temp_dummy_table_3 VALUES ('2023-11-25 00:00:00');
        """
    )

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    etl = ETL(ppss, gql_data_factory)
    etl.bronze_table_names = [
        "test_bronze_table_1",
        "test_bronze_table_2",
        "test_bronze_table_3",
    ]
    etl.raw_table_names = ["dummy_table_1", "dummy_table_2", "dummy_table_3"]
    from_timestamp, to_timestamp = etl._calc_bronze_start_end_ts()

    assert to_timestamp.strftime("%Y-%m-%d %H:%M:%S") == "2023-11-21 00:00:00"
    assert from_timestamp.strftime("%Y-%m-%d %H:%M:%S") == "2023-11-02 00:00:00"
