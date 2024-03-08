from io import StringIO
import os
import sys

from polars import Boolean, Float64, Int64, Utf8
import polars as pl
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.table import Table
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
    predictions_table_name,
)
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.persistent_data_store import PersistentDataStore


def _check_view_exists(persistent_data_store, table_name):
    tables = persistent_data_store.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    return [table_name in [table[0] for table in tables], table_name]


def _clean_up_persistent_data_store(tmpdir, table_name):
    # Clean up PDS
    persistent_data_store = PersistentDataStore(str(tmpdir))

    # Select tables from duckdb
    views = persistent_data_store.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()

    # Drop the view and table
    if table_name in [table[0] for table in views]:
        persistent_data_store.duckdb_conn.execute(f"DROP TABLE {table_name}")


def test_table_initialization(tmpdir):
    """
    Test that show Table initializing correctly
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    # TODO - PPSS should be using tmpdir

    table = Table(predictions_table_name, predictions_schema, ppss)

    assert table.table_name == predictions_table_name
    assert table.ppss.lake_ss.st_timestr == st_timestr
    assert table.ppss.lake_ss.fin_timestr == fin_timestr


def test_csv_data_store(
    _gql_datafactory_first_predictions_df,
    tmpdir,
):
    """
    Test that create table and append existing mock prediction data
    """
    st_timestr = "2023-11-01"
    fin_timestr = "2024-11-03"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    # Initialize Table, fill with data, validate
    table = Table(predictions_table_name, predictions_schema, ppss)
    table._append_to_csv(_gql_datafactory_first_predictions_df)

    assert table.csv_data_store.has_data(predictions_table_name)

    print(os.listdir(os.path.join(ppss.lake_ss.parquet_dir,table.table_name)))

    file_path = os.path.join(
        ppss.lake_ss.parquet_dir,
        table.table_name,
        f"{table.table_name}_from_1701503000000_to_.csv",
    )

    assert os.path.exists(file_path)

    with open(file_path, "r") as file:
        lines = file.readlines()
        assert len(lines) == 3

    # TODO - Add support for verifying 1001 rows
    #     with open(file_path, "r") as file:
    #         lines = file.readlines()
    #         assert len(lines) == 1001


def test_persistent_store(
    _gql_datafactory_first_predictions_df,
    _gql_datafactory_second_predictions_df,
    tmpdir,
):
    """
    Test that create table and append existing mock prediction data
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    # Initialize Table, fill with data, validate
    table = Table(predictions_table_name, predictions_schema, ppss)

    table.PDS._create_and_fill_table(
        _gql_datafactory_first_predictions_df, predictions_table_name
    )

    assert _check_view_exists(table.PDS, predictions_table_name)

    result = table.PDS.query_data(f"SELECT * FROM {predictions_table_name}")
    assert len(result) == 2, "Length of the table is not as expected"

    # Add second batch of predictions, validate
    table.PDS.insert_to_table(
        _gql_datafactory_second_predictions_df, predictions_table_name
    )

    result = table.PDS.query_data(f"SELECT * FROM {predictions_table_name}")

    assert len(result) == 8, "Length of the table is not as expected"

    assert result["ID"][0] == "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1701503100-0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    assert result["pair"][0] == "ADA/USDT"
    assert result["timeframe"][0] == "5m"
    assert result["predvalue"][0] is True
    assert len(result) == 8
