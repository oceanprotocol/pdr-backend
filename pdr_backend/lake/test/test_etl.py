#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import Mock, patch

import polars as pl
import pytest
from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.etl import (
    _ETL_REGISTERED_LAKE_TABLES,
    _ETL_REGISTERED_TABLE_NAMES,
    ETL,
)
from pdr_backend.lake.gql_data_factory import _GQLDF_REGISTERED_LAKE_TABLES
from pdr_backend.lake.table import ETLTable, NamedTable, TempTable
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction
from pdr_backend.lake.table_bronze_pdr_slots import BronzeSlot
from pdr_backend.lake.test.resources import _gql_data_factory
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
    _, db, gql_tables = setup_data

    # Assert all dfs are not the same size as mock data
    pdr_predictions_df = db.query_data("SELECT * FROM pdr_predictions")
    pdr_payouts_df = db.query_data("SELECT * FROM pdr_payouts")
    pdr_truevals_df = db.query_data("SELECT * FROM pdr_truevals")
    pdr_slots_df = db.query_data("SELECT * FROM pdr_slots")
    assert len(pdr_predictions_df) != len(_gql_datafactory_etl_predictions_df)
    assert len(pdr_payouts_df) != len(_gql_datafactory_etl_payouts_df)
    assert len(pdr_truevals_df) != len(_gql_datafactory_etl_truevals_df)

    # Assert len of all dfs
    assert len(gql_tables) == len(_GQLDF_REGISTERED_LAKE_TABLES) + len(
        _ETL_REGISTERED_LAKE_TABLES
    )
    assert len(pdr_slots_df) == 6
    assert len(pdr_predictions_df) == 5
    assert len(pdr_payouts_df) == 4
    assert len(pdr_truevals_df) == 5


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
    etl, db, _ = setup_data

    # Work 1: Do bronze
    etl.do_bronze_step()
    etl._move_from_temp_tables_to_live()

    # assert bronze_pdr_predictions_df is created
    table_name = NamedTable.from_dataclass(BronzePrediction).fullname
    bronze_pdr_predictions_records = db.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    assert len(bronze_pdr_predictions_records) == 5
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
    table_name = NamedTable.from_dataclass(BronzeSlot).fullname
    bronze_pdr_slots_records = db.query_data("SELECT * FROM {}".format(table_name))

    assert bronze_pdr_slots_records is None


@pytest.mark.parametrize(
    "setup_data", [("2023-11-02_0:00", "2023-11-07_0:00")], indirect=True
)
def test_etl_views(setup_data):
    etl, db, _ = setup_data

    # Work 1: First Run
    with patch("pdr_backend.lake.etl.ETL._move_from_temp_tables_to_live") as mock:
        etl.do_bronze_step()
        etl._move_from_temp_tables_to_live()
        assert mock.called

    # live table shouldn't exist
    # temp table should be created
    # etl view shouldn't exist
    assert not BronzePrediction.get_lake_table_name() in db.get_table_names()
    records = db.query_data(
        "SELECT * FROM {}".format(TempTable.from_dataclass(BronzePrediction).fullname)
    )
    assert len(records) == 5
    assert ETLTable.from_dataclass(BronzePrediction).fullname in db.get_view_names()

    # move from temp to live
    etl._move_from_temp_tables_to_live()


@enforce_types
@pytest.mark.parametrize(
    "setup_data", [("2023-11-02_0:00", "2023-11-07_0:00")], indirect=True
)
def test_drop_temp_sql_tables(setup_data):
    etl, db, _ = setup_data

    # SELECT ALL TABLES FROM DB
    table_names = db.get_table_names()

    # DROP ALL TABLES
    for table in table_names:
        db.duckdb_conn.execute(f"DROP TABLE {table}")

    dummy_schema = {"test_column": str}

    # Insert temp ETL tables w/ dummy data into DuckDB
    for table_name in _ETL_REGISTERED_TABLE_NAMES:
        db.insert_from_df(
            pl.DataFrame([], schema=dummy_schema), TempTable(table_name).fullname
        )

    # assert all ETL temp tables were created
    etl_table_names = db.get_table_names()
    assert len(etl_table_names) == len(_ETL_REGISTERED_TABLE_NAMES)

    # now, drop all ETL temp tables and verify we're back to 0
    etl._drop_temp_sql_tables()

    table_names = db.get_table_names()

    assert len(table_names) == 0


@enforce_types
@pytest.mark.parametrize(
    "setup_data", [("2023-11-02_0:00", "2023-11-07_0:00")], indirect=True
)
def test_move_from_temp_tables_to_live(setup_data):
    etl, db, gql_tables = setup_data

    # Insert temp ETL tables w/ dummy data into DuckDB
    temp_bronze_table_names = []
    dummy_schema = {"test_column": str}
    for table_name in _ETL_REGISTERED_TABLE_NAMES:
        db.insert_from_df(
            pl.DataFrame([], schema=dummy_schema), TempTable(table_name).fullname
        )
        temp_bronze_table_names.append(TempTable(table_name).fullname)

    # check if tables are created
    table_names = db.get_table_names()

    # Assert all temp bronze table names exist in table_names
    assert all(
        table in table_names for table in temp_bronze_table_names
    ), "Not all temporary bronze tables were created successfully"

    etl._move_from_temp_tables_to_live()

    # check all temp tables are dropped, and raw + etl exist
    table_names = db.get_table_names()
    assert all(
        table in table_names for table in _ETL_REGISTERED_TABLE_NAMES
    ), "Not all temporary bronze tables were moved to live tables successfully"
    assert len(table_names) == len(gql_tables) + len(_ETL_REGISTERED_TABLE_NAMES)

    # Verify no build tables exist
    table_names = db.get_table_names()
    for table_name in table_names:
        assert "_temp_" not in table_name


@enforce_types
def test_get_max_timestamp_values_from(tmpdir):
    db = DuckDBDataStore(str(tmpdir))

    db.duckdb_conn.execute(
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
    db.duckdb_conn.execute(
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
    db = DuckDBDataStore(str(tmpdir))

    # mock bronze + raw tables
    db.duckdb_conn.execute(
        """
        CREATE TABLE raw_table_1 (timestamp INT64);
        CREATE TABLE raw_table_2 (timestamp INT64);
        CREATE TABLE raw_table_3 (timestamp INT64);
        """
    )

    db.duckdb_conn.execute(
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
    db.duckdb_conn.execute(
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
    db.duckdb_conn.execute(
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
        1. ETL step resumes from max(timestamp) across all bronze tables
        - this gets the "checkpoint" from where the ETL pipeline last ended/should resume
        - this gives us our "from" timestamp
        2. raw_tables can have different max timestamps
        - db raw tables should have just been updated by GQLDF
        - this gives us our "to" timestamp
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

    gql_data_factory = Mock(spec=gql_data_factory)
    mock_gql_tables = [
        "raw_table_1",
        "raw_table_2",
        "raw_table_3",
    ]

    etl = ETL(ppss, gql_data_factory)
    mock_tables = [
        "bronze_table_1",
        "bronze_table_2",
        "bronze_table_3",
    ]

    with patch("pdr_backend.lake.etl._ETL_REGISTERED_TABLE_NAMES", mock_tables):
        with patch(
            "pdr_backend.lake.etl._GQLDF_REGISTERED_TABLE_NAMES", mock_gql_tables
        ):
            # Calculate from + to timestamps
            from_timestamp, to_timestamp = etl._calc_bronze_start_end_ts()

    assert (
        UnixTimeMs(from_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 00:00:00"
    )
    assert (
        UnixTimeMs(to_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-25 00:00:00"
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
    from_timestamp, to_timestamp = etl._calc_bronze_start_end_ts()

    ts_now = UnixTimeMs.now()
    assert (
        UnixTimeMs(from_timestamp).to_dt().strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 00:00:00"
    )
    assert abs(ts_now - to_timestamp) < 100
