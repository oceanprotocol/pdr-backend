from unittest.mock import patch
import pytest
from enforce_typing import enforce_types

import polars as pl
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.etl import ETL
from pdr_backend.lake.table import TableType, get_table_name, NamedTable
from pdr_backend.lake.table_registry import TableRegistry
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_table_name,
)
from pdr_backend.lake.table_bronze_pdr_slots import bronze_pdr_slots_table_name
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
@pytest.mark.parametrize(
    "setup_data", [("2023-11-02_0:00", "2023-11-07_0:00")], indirect=True
)
def test_etl_tables(
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_truevals_df,
    setup_data,
):
    _, pds, _ = setup_data

    # Assert all dfs are not the same size as mock data
    pdr_predictions_df = pds.query_data("SELECT * FROM pdr_predictions")
    pdr_payouts_df = pds.query_data("SELECT * FROM pdr_payouts")
    pdr_truevals_df = pds.query_data("SELECT * FROM pdr_truevals")
    pdr_slots_df = pds.query_data("SELECT * FROM pdr_slots")
    assert len(pdr_predictions_df) != len(_gql_datafactory_etl_predictions_df)
    assert len(pdr_payouts_df) != len(_gql_datafactory_etl_payouts_df)
    assert len(pdr_truevals_df) != len(_gql_datafactory_etl_truevals_df)

    # Assert len of all dfs
    assert len(pdr_slots_df) == 6
    assert len(pdr_predictions_df) == 5
    assert len(pdr_payouts_df) == 4
    assert len(pdr_predictions_df) == 5
    assert len(pdr_truevals_df) == 5
    assert len(TableRegistry().get_tables()) == 7


# pylint: disable=too-many-statements
@enforce_types
@pytest.mark.parametrize(
    "setup_data", [("2023-11-02_0:00", "2023-11-07_0:00")], indirect=True
)
def test_etl_do_bronze_step(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    setup_data,
):
    etl, pds, _ = setup_data

    # Work 1: Do bronze
    etl.do_bronze_step()
    etl._move_from_temp_tables_to_live()

    # assert bronze_pdr_predictions_df is created
    table_name = get_table_name(bronze_pdr_predictions_table_name)
    bronze_pdr_predictions_records = pds.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    assert len(bronze_pdr_predictions_records) == 5

    # TODO:
    assert len(_gql_datafactory_etl_predictions_df) == 6

    print(f"bronze_pdr_predictions_records {bronze_pdr_predictions_records}")

    # Assert that "contract" data was created, and matches the same data from pdr_predictions
    bronze_pdr_predictions_df = bronze_pdr_predictions_records
    assert (
        bronze_pdr_predictions_df["contract"][0]
        == _gql_datafactory_etl_predictions_df["contract"][1]
    )
    assert (
        bronze_pdr_predictions_df["contract"][1]
        == _gql_datafactory_etl_predictions_df["contract"][2]
    )
    assert (
        bronze_pdr_predictions_df["contract"][2]
        == _gql_datafactory_etl_predictions_df["contract"][3]
    )

    # Assert timestamp == predictions timestamp
    assert (
        bronze_pdr_predictions_df["timestamp"][1]
        == _gql_datafactory_etl_predictions_df["timestamp"][2]
    )
    assert (
        bronze_pdr_predictions_df["timestamp"][2]
        == _gql_datafactory_etl_predictions_df["timestamp"][3]
    )

    # Assert last_event_timestamp == payout.timestamp
    assert (
        bronze_pdr_predictions_df["last_event_timestamp"][1]
        == _gql_datafactory_etl_payouts_df["timestamp"][2]
    )
    assert (
        bronze_pdr_predictions_df["last_event_timestamp"][2]
        == _gql_datafactory_etl_payouts_df["timestamp"][3]
    )

    # Assert predictions.truevalue == gql truevals_df
    assert bronze_pdr_predictions_df["truevalue"][2] is True
    assert bronze_pdr_predictions_df["truevalue"][3] is False

    print(bronze_pdr_predictions_df["truevalue"])
    print(_gql_datafactory_etl_truevals_df["truevalue"])

    assert (
        bronze_pdr_predictions_df["truevalue"][1]
        == _gql_datafactory_etl_truevals_df["truevalue"][2]
    )
    assert (
        bronze_pdr_predictions_df["truevalue"][2]
        == _gql_datafactory_etl_truevals_df["truevalue"][3]
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
        _gql_datafactory_etl_payouts_df["payout"][2], 3
    )
    assert round(bronze_pdr_predictions_df["payout"][2], 3) == round(
        _gql_datafactory_etl_payouts_df["payout"][3], 3
    )

    # Assert stake in the bronze_table came from payouts
    assert round(bronze_pdr_predictions_df["stake"][1], 3) == round(
        _gql_datafactory_etl_payouts_df["stake"][2], 3
    )
    assert round(bronze_pdr_predictions_df["stake"][2], 3) == round(
        _gql_datafactory_etl_payouts_df["stake"][3], 3
    )

    # Assert bronze slots table is building correctly
    table_name = get_table_name(bronze_pdr_slots_table_name)
    bronze_pdr_slots_records = pds.query_data("SELECT * FROM {}".format(table_name))

    assert len(bronze_pdr_slots_records) == 4
    assert bronze_pdr_slots_records["truevalue"].null_count() == 1
    assert bronze_pdr_slots_records["roundSumStakes"].null_count() == 1
    assert bronze_pdr_slots_records["source"].null_count() == 1


@pytest.mark.parametrize(
    "setup_data", [("2023-11-02_0:00", "2023-11-07_0:00")], indirect=True
)
def test_etl_views(setup_data):
    etl, pds, _ = setup_data

    # Work 1: First Run
    with patch("pdr_backend.lake.etl.ETL._move_from_temp_tables_to_live") as mock:
        etl.do_bronze_step()
        etl._move_from_temp_tables_to_live()
        assert mock.called

    # live table shouldn't exist
    # temp table should be created
    # etl view shouldn't exist
    assert not bronze_pdr_predictions_table_name in pds.get_table_names()
    records = pds.query_data(
        "SELECT * FROM {}".format(
            get_table_name(bronze_pdr_predictions_table_name, TableType.TEMP)
        )
    )
    assert len(records) == 5
    assert (
        get_table_name(bronze_pdr_predictions_table_name, TableType.ETL)
        in pds.get_view_names()
    )

    # move from temp to live
    etl._move_from_temp_tables_to_live()


@enforce_types
@pytest.mark.parametrize(
    "setup_data", [("2023-11-02_0:00", "2023-11-07_0:00")], indirect=True
)
def test_drop_temp_sql_tables(setup_data):
    etl, pds, _ = setup_data

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
@pytest.mark.parametrize(
    "setup_data", [("2023-11-02_0:00", "2023-11-07_0:00")], indirect=True
)
def test_move_from_temp_tables_to_live(setup_data):
    etl, pds, gql_tables = setup_data
    assert len(gql_tables) == 5

    dummy_schema = {"test_column": str}
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_a")
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_b")
    pds.insert_to_table(pl.DataFrame([], schema=dummy_schema), "_temp_c")

    # check if tables are created
    table_names = pds.get_table_names()
    etl.temp_table_names = ["a", "b", "c"]
    etl._move_from_temp_tables_to_live()

    # check "c" exists in permanent tables
    table_names = pds.get_table_names()
    assert len(table_names) == 8
    assert "c" in table_names
    assert "a" in table_names
    assert "b" in table_names

    # Verify no build tables exist
    table_names = pds.get_table_names()
    for table_name in table_names:
        assert "_temp_" not in table_name


@enforce_types
def test_get_max_timestamp_values_from(tmpdir):
    pds = PersistentDataStore(str(tmpdir))

    pds.duckdb_conn.execute(
        """
        CREATE TABLE test_table_1 (timestamp INT64);
        CREATE TABLE test_table_2 (timestamp INT64);
        CREATE TABLE test_table_3 (timestamp INT64);
        """
    )

    ts1 = UnixTimeMs.from_timestr("2023-11-02_0:00")
    ts2 = UnixTimeMs.from_timestr("2023-11-03_0:00")
    ts3 = UnixTimeMs.from_timestr("2023-11-04_0:00")
    ts4 = UnixTimeMs.from_timestr("2023-11-09_0:00")
    pds.duckdb_conn.execute(
        """
        INSERT INTO test_table_1 VALUES (INT64 '{0}');
        INSERT INTO test_table_2 VALUES (INT64 '{1}');
        INSERT INTO test_table_2 VALUES (INT64 '{2}');
        INSERT INTO test_table_3 VALUES (INT64 '{3}');
        """.format(
            ts1, ts2, ts3, ts4
        )
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
        [
            NamedTable("test_table_1"),
            NamedTable("test_table_2"),
            NamedTable("test_table_3"),
        ]
    )
    assert (
        UnixTimeMs(max_timestamp_values["test_table_1"])
        .to_dt()
        .strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 00:00:00"
    )
    assert (
        UnixTimeMs(max_timestamp_values["test_table_2"])
        .to_dt()
        .strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-04 00:00:00"
    )
    assert (
        UnixTimeMs(max_timestamp_values["test_table_3"])
        .to_dt()
        .strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-09 00:00:00"
    )


@enforce_types
def _fill_dummy_tables(tmpdir):
    pds = PersistentDataStore(str(tmpdir))

    # mock bronze + raw tables
    pds.duckdb_conn.execute(
        """
        CREATE TABLE raw_table_1 (timestamp INT64);
        CREATE TABLE raw_table_2 (timestamp INT64);
        CREATE TABLE raw_table_3 (timestamp INT64);
        """
    )

    pds.duckdb_conn.execute(
        """
        CREATE TABLE bronze_table_1 (timestamp INT64);
        CREATE TABLE bronze_table_2 (timestamp INT64);
        CREATE TABLE bronze_table_3 (timestamp INT64);
        """
    )

    # all bronze tables should have the same max timestamp
    # etl should start from the bronze table max_timestamp => 2023-11-02
    ts1 = UnixTimeMs.from_timestr("2023-11-01_0:00")
    ts2 = UnixTimeMs.from_timestr("2023-11-02_0:00")
    pds.duckdb_conn.execute(
        """
        INSERT INTO bronze_table_1 VALUES (INT64 '{1}');
        INSERT INTO bronze_table_2 VALUES (INT64 '{0}');
        INSERT INTO bronze_table_2 VALUES (INT64 '{1}');
        INSERT INTO bronze_table_3 VALUES (INT64 '{1}');
        """.format(
            ts1, ts2
        )
    )

    # raw tables can have different max timestamps
    # etl should process all raw_tables up to min_timestamp => 2023-11-21
    ts1 = UnixTimeMs.from_timestr("2023-11-21_0:00")
    ts2 = UnixTimeMs.from_timestr("2023-11-22_0:00")
    ts3 = UnixTimeMs.from_timestr("2023-11-23_0:00")
    ts4 = UnixTimeMs.from_timestr("2023-11-25_0:00")
    pds.duckdb_conn.execute(
        """
        INSERT INTO raw_table_1 VALUES (INT64 '{0}');
        INSERT INTO raw_table_2 VALUES (INT64 '{1}');
        INSERT INTO raw_table_2 VALUES (INT64 '{2}');
        INSERT INTO raw_table_3 VALUES (INT64 '{3}');
        """.format(
            ts1, ts2, ts3, ts4
        )
    )


@enforce_types
def test_calc_bronze_start_end_ts(tmpdir):
    """
    @description
        Verify that the start and end timestamps for the bronze tables are calculated correctly
        1. ETL step starts from bronze_table max timestamp
        2. raw_tables can have different max timestamps
        3. bronze_tables should have the same max timestamp
    """
    _fill_dummy_tables(tmpdir)

    # we can set whatever we want here, the ETL pipeline should update as best as possible
    st_timestr = "2023-11-01_0:00"
    fin_timestr = "2023-11-30_0:00"

    # Setup GQL Data Factory and mock tables for ETL
    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    etl = ETL(ppss, gql_data_factory)
    etl.raw_table_names = ["raw_table_1", "raw_table_2", "raw_table_3"]
    etl.bronze_table_names = [
        "bronze_table_1",
        "bronze_table_2",
        "bronze_table_3",
    ]

    # Calculate from + to timestamps
    from_timestamp, to_timestamp = etl._calc_bronze_start_end_ts()

    assert (
        UnixTimeMs(from_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 00:00:00"
    )
    assert (
        UnixTimeMs(to_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-21 00:00:00"
    )


@enforce_types
def test_calc_bronze_start_end_ts_with_nonexist_tables(tmpdir):
    _fill_dummy_tables(tmpdir)

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
        "bronze_table_1",
        "bronze_table_2",
        "bronze_table_3",
        "bronze_table_4",
        "bronze_table_5",
    ]
    etl.raw_table_names = [
        "dummy_table_1",
        "dummy_table_2",
        "dummy_table_3",
        "dummy_table_4",
        "dummy_table_5",
    ]
    from_timestamp, to_timestamp = etl._calc_bronze_start_end_ts()

    assert (
        UnixTimeMs(from_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 00:00:00"
    )
    assert (
        UnixTimeMs(to_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-07 00:00:00"
    )


@enforce_types
def test_calc_bronze_start_end_ts_with_now_value(tmpdir):
    _fill_dummy_tables(tmpdir)

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "now"

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    etl = ETL(ppss, gql_data_factory)
    etl.bronze_table_names = [
        "bronze_table_1",
        "bronze_table_2",
        "bronze_table_3",
    ]
    etl.raw_table_names = ["dummy_table_1", "dummy_table_2", "dummy_table_3"]
    from_timestamp, to_timestamp = etl._calc_bronze_start_end_ts()

    ts_now = UnixTimeMs.now()
    assert (
        UnixTimeMs(from_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 00:00:00"
    )
    assert abs(ts_now - to_timestamp) < 100


@enforce_types
def test_calc_bronze_start_end_ts_with_now_value_and_nonexist_tables(tmpdir):
    _fill_dummy_tables(tmpdir)

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "now"

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    etl = ETL(ppss, gql_data_factory)
    etl.bronze_table_names = [
        "bronze_table_1",
        "bronze_table_2",
        "bronze_table_3",
        "bronze_table_4",
        "bronze_table_5",
    ]
    etl.raw_table_names = [
        "dummy_table_1",
        "dummy_table_2",
        "dummy_table_3",
        "dummy_table_4",
        "dummy_table_5",
    ]
    from_timestamp, to_timestamp = etl._calc_bronze_start_end_ts()

    ts_now = UnixTimeMs.now()
    assert (
        UnixTimeMs(from_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 00:00:00"
    )
    assert abs(ts_now - to_timestamp) < 100
