import os
from io import StringIO
from polars import Boolean, Float64, Int64, Utf8
import polars as pl
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.table import Table
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
    predictions_table_name,
)

from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.csv_data_store import CSVDataStore


# pylint: disable=too-many-instance-attributes
class MyClass:
    def __init__(self, data):
        self.ID = data["ID"]
        self.pair = data["pair"]
        self.timeframe = data["timeframe"]
        self.prediction = data["prediction"]
        self.payout = data["payout"]
        self.timestamp = data["timestamp"]
        self.slot = data["slot"]
        self.user = data["user"]


mocked_object = {
    "ID": "0x123",
    "pair": "ADA-USDT",
    "timeframe": "5m",
    "prediction": True,
    "payout": 28.2,
    "timestamp": 1701634400000,
    "slot": 1701634400000,
    "user": "0x123",
}


def mock_fetch_function(
    network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
):
    print(network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config)
    return [MyClass(mocked_object)]


def get_table_df(network, st_ut, fin_ut, config):
    print(network, st_ut, fin_ut, config)
    return pl.DataFrame([mocked_object], table_df_schema)


table_df_schema = {
    "ID": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "prediction": Boolean,
    "payout": Float64,
    "timestamp": Int64,
    "slot": Int64,
    "user": Utf8,
}
table_name = "pdr_test_df"
file_path = f"./parquet_data/{table_name}.parquet"
file_path2 = "./parquet_data/test_prediction_table_multiple.parquet"

# delete test file if already exists
if os.path.exists(file_path):
    os.remove(file_path)
if os.path.exists(file_path2):
    os.remove(file_path2)


def _table_exists(persistent_data_store, searched_table_name):
    table_names = persistent_data_store.get_table_names()
    return [searched_table_name in table_names, table_name]


def test_table_initialization(tmpdir):
    """
    Test that show Table initializing correctly
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table(predictions_table_name, predictions_schema, ppss)

    assert table.table_name == predictions_table_name
    assert table.ppss.lake_ss.st_timestr == st_timestr
    assert table.ppss.lake_ss.fin_timestr == fin_timestr


def test_csv_data_store(
    _gql_datafactory_first_predictions_df,
    _gql_datafactory_1k_predictions_df,
    tmpdir,
):
    """
    Test that create table and append existing mock prediction data
    """
    st_timestr = "2023-11-01"
    fin_timestr = "2024-11-03"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    # Initialize Table, fill with data, validate
    table = Table(predictions_table_name, predictions_schema, ppss)
    table._append_to_csv(_gql_datafactory_first_predictions_df)

    assert CSVDataStore(table.base_path).has_data(predictions_table_name)

    csv_file_path = os.path.join(
        ppss.lake_ss.lake_dir,
        table.table_name,
        f"{table.table_name}_from_1701503000000_to_.csv",
    )

    assert os.path.exists(csv_file_path)

    with open(csv_file_path, "r") as file:
        lines = file.readlines()
        assert len(lines) == 3
        file.close()

    # Add second batch of predictions, validate
    table._append_to_csv(_gql_datafactory_1k_predictions_df)

    files = os.listdir(os.path.join(ppss.lake_ss.lake_dir, table.table_name))
    files.sort(reverse=True)

    assert len(files) == 2

    new_file_path = os.path.join(
        ppss.lake_ss.lake_dir,
        table.table_name,
        files[0],
    )
    with open(new_file_path, "r") as file:
        lines = file.readlines()
        assert len(lines) == 3


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
        [{"train_on": "binance BTC/USDT c 5m", "predict": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    # Initialize Table, fill with data, validate
    PDS = PersistentDataStore(ppss.lake_ss.lake_dir)
    PDS._create_and_fill_table(
        _gql_datafactory_first_predictions_df, predictions_table_name
    )

    assert _table_exists(PDS, predictions_table_name)

    result = PDS.query_data(f"SELECT * FROM {predictions_table_name}")
    assert len(result) == 2, "Length of the table is not as expected"

    # Add second batch of predictions, validate
    PDS.insert_to_table(_gql_datafactory_second_predictions_df, predictions_table_name)

    result = PDS.query_data(f"SELECT * FROM {predictions_table_name}")

    assert len(result) == 8, "Length of the table is not as expected"

    assert (
        result["ID"][0]
        == "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1701503100-0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"  # pylint: disable=line-too-long
    )
    assert result["pair"][0] == "ADA/USDT"
    assert result["timeframe"][0] == "5m"
    assert result["predvalue"][0] is True
    assert len(result) == 8


def test_append_to_db(caplog):
    """
    Test that table is saving to local file
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table(table_name, table_df_schema, ppss)
    data = pl.DataFrame([mocked_object], table_df_schema)
    table._append_to_db(data)

    assert f"Appended 1 rows to db table: {table_name}" in caplog.text
