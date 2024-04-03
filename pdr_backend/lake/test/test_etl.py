import pytest
from enforce_typing import enforce_types

import polars as pl
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.etl import ETL
from pdr_backend.lake.table import Table, TableType, get_table_name
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
from pdr_backend.lake.table import get_table_name, TableType
from pdr_backend.lake.table_pdr_slots import slots_schema, slots_table_name
from pdr_backend.lake.table_pdr_subscriptions import (
    subscriptions_table_name,
    subscriptions_schema,
)
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_table_name,
)
from pdr_backend.lake.table_bronze_pdr_slots import bronze_pdr_slots_table_name


@enforce_types
def get_filtered_timestamps_df(
    df: pl.DataFrame, st_timestr: str, fin_timestr: str
) -> pl.DataFrame:
    return df.filter(
        (pl.col("timestamp") >= UnixTimeMs.from_timestr(st_timestr))
        & (pl.col("timestamp") <= UnixTimeMs.from_timestr(fin_timestr))
    )

@pytest.fixture
def setup_data(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    _gql_datafactory_etl_slots_df,
    _get_test_PDS,
    tmpdir,
    request):
    _clean_up_persistent_data_store(tmpdir)
    _clean_up_table_registry()

    st_timestr = request.param[0]
    fin_timestr = request.param[1]

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
        "pdr_slots": Table(slots_table_name, slots_schema, ppss),
        "pdr_subscriptions": Table(subscriptions_table_name, subscriptions_schema, ppss),
    }

    gql_tables["pdr_predictions"].append_to_storage(preds)
    gql_tables["pdr_truevals"].append_to_storage(truevals)
    gql_tables["pdr_payouts"].append_to_storage(payouts)
    gql_tables["pdr_slots"].append_to_storage(slots)
    gql_tables["pdr_subscriptions"].append_to_storage(slots)

    assert ppss.lake_ss.st_timestamp == UnixTimeMs.from_timestr(st_timestr)
    assert ppss.lake_ss.fin_timestamp == UnixTimeMs.from_timestr(fin_timestr)

    # provide the setup data to the test
    etl = ETL(ppss, gql_data_factory)
    pds = _get_test_PDS(tmpdir)
    
    assert etl is not None
    assert etl.gql_data_factory == gql_data_factory

    table_name = get_table_name("pdr_predictions")
    _records = pds.query_data("SELECT * FROM {}".format(table_name))
    assert len(_records) == 5

    yield etl, pds, gql_tables

@enforce_types
@pytest.mark.parametrize('setup_data', [("2023-11-02_0:00", '2023-11-07_0:00')], indirect=True)
def test_etl_tables(
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_truevals_df,
    setup_data):
    etl, pds, gql_tables = setup_data

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
@pytest.mark.parametrize('setup_data', [("2023-11-02_0:00", '2023-11-07_0:00')], indirect=True)
def test_etl_do_bronze_step(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    setup_data
):
    etl, pds, gql_tables = setup_data
    
    # Work 1: Do bronze
    etl.do_bronze_step()

    # assert bronze_pdr_predictions_df is created
    temp_table_name = get_table_name(bronze_pdr_predictions_table_name, TableType.TEMP)
    bronze_pdr_predictions_records = pds.query_data(
        "SELECT * FROM {}".format(temp_table_name)
    )
    assert len(bronze_pdr_predictions_records) == 6

    # Assert that "contract" data was created, and matches the same data from pdr_predictions
    bronze_pdr_predictions_df = bronze_pdr_predictions_records
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

    # Assert bronze slots table is building correctly
    temp_bronze_pdr_slots_table_name = get_table_name(
        bronze_pdr_slots_table_name, TableType.TEMP
    )
    bronze_pdr_slots_records = pds.query_data(
        "SELECT * FROM {}".format(temp_bronze_pdr_slots_table_name)
    )
    print("bronze_pdr_slots_records---1", bronze_pdr_slots_records)

    assert len(bronze_pdr_slots_records) == 5
    assert bronze_pdr_slots_records["truevalue"].null_count() == 0
    assert bronze_pdr_slots_records["roundSumStakes"].null_count() == 1
    assert bronze_pdr_slots_records["source"].null_count() == 1

@pytest.mark.parametrize('setup_data', [("2023-11-02_0:00", '2023-11-07_0:00')], indirect=True)
def test_etl_views(setup_data):
    etl, pds, gql_tables = setup_data
    etl.do_bronze_step()

    # assert views are working
    etl.create_etl_view("pdr_predictions")
    df = pds.query_data("SELECT * FROM _etl_pdr_predictions").pl()
    assert len(df) == 5
    
    # Assert number of views is equal to 1
    view_names = pds.get_view_names()
    assert len(view_names) == 1
    print(f"view_names are {view_names}")

    # Assert view is registered
    check_result = pds.view_exists("_etl_pdr_predictions")
    print(f"check_result is {check_result}")
    assert check_result == True

@enforce_types
@pytest.mark.parametrize('setup_data', [("2023-11-02_0:00", '2023-11-07_0:00')], indirect=True)
def test_drop_temp_sql_tables(setup_data):
    etl, pds, gql_tables = setup_data

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
@pytest.mark.parametrize('setup_data', [("2023-11-02_0:00", '2023-11-07_0:00')], indirect=True)
def test_move_from_temp_tables_to_live(setup_data):
    etl, pds, gql_tables = setup_data

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
    """
    @description
        Verify that the start and end timestamps for the bronze tables are calculated correctly
        1. ETL step starts from bronze_table max timestamp
        2. raw_tables can have different max timestamps
        3. bronze_tables should have the same max timestamp
    """
    _clean_up_persistent_data_store(tmpdir)
    pds = PersistentDataStore(str(tmpdir))

    # mock bronze + raw tables
    pds.duckdb_conn.execute(
        """
        CREATE TABLE raw_table_1 (timestamp TIMESTAMP);
        CREATE TABLE raw_table_2 (timestamp TIMESTAMP);
        CREATE TABLE raw_table_3 (timestamp TIMESTAMP);
        """
    )

    pds.duckdb_conn.execute(
        """
        CREATE TABLE bronze_table_1 (timestamp TIMESTAMP);
        CREATE TABLE bronze_table_2 (timestamp TIMESTAMP);
        CREATE TABLE bronze_table_3 (timestamp TIMESTAMP);
        """
    )

    # all bronze tables should have the same max timestamp
    # etl should start from the bronze table max_timestamp => 2023-11-02
    pds.duckdb_conn.execute(
        """
        INSERT INTO bronze_table_1 VALUES ('2023-11-02 00:00:00');
        INSERT INTO bronze_table_2 VALUES ('2023-11-01 00:00:00');
        INSERT INTO bronze_table_2 VALUES ('2023-11-02 00:00:00');
        INSERT INTO bronze_table_3 VALUES ('2023-11-02 00:00:00');
        """
    )

    # raw tables can have different max timestamps
    # etl should process all raw_tables up to min_timestamp => 2023-11-21
    pds.duckdb_conn.execute(
        """
        INSERT INTO raw_table_1 VALUES ('2023-11-21 00:00:00');
        INSERT INTO raw_table_2 VALUES ('2023-11-23 00:00:00');
        INSERT INTO raw_table_2 VALUES ('2023-11-22 00:00:00');
        INSERT INTO raw_table_3 VALUES ('2023-11-25 00:00:00');
        """
    )

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

    # Assert ETL starts from bronze tables max timestamp
    # Assert ETL processes raw tables up-to the common min_timestamp between them
    assert from_timestamp.strftime("%Y-%m-%d %H:%M:%S") == "2023-11-02 00:00:00"
    assert to_timestamp.strftime("%Y-%m-%d %H:%M:%S") == "2023-11-21 00:00:00"
