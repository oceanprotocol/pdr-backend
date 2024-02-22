from io import StringIO
import os
import sys
from polars import Boolean, Float64, Int64, Utf8
import polars as pl
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.table import Table
from pdr_backend.subgraph.subgraph_predictions import fetch_filtered_predictions
from pdr_backend.lake.table_pdr_predictions import predictions_schema


# pylint: disable=too-many-instance-attributes
class MyClass:
    def __init__(self, data):
        self.ID = data["ID"]
        self.pair = data["pair"]
        self.timeframe = data["timeframe"]
        self.predvalue = data["predvalue"]
        self.payout = data["payout"]
        self.timestamp = data["timestamp"]
        self.slot = data["slot"]
        self.user = data["user"]


mocked_object = {
    "ID": "0x123",
    "pair": "ADA-USDT",
    "timeframe": "5m",
    "predvalue": True,
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
    "predvalue": Boolean,
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


def test_table_initialization():
    """
    Test that table is initialized correctly
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

    table = Table(table_name, table_df_schema, ppss)
    assert len(table.df) == 0
    assert table.df.columns == table.df.columns
    assert table.df.dtypes == table.df.dtypes
    assert table.table_name == table_name
    assert table.ppss.lake_ss.st_timestr == st_timestr
    assert table.ppss.lake_ss.fin_timestr == fin_timestr


def test_load_table():
    """
    Test that table is loading the data from file
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

    table = Table(table_name, table_df_schema, ppss)
    table.load()

    assert len(table.df) == 0


def test_save_table():
    """
    Test that table is saving to local file
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table(table_name, table_df_schema, ppss)

    captured_output = StringIO()
    sys.stdout = captured_output

    assert len(table.df) == 0
    table.df = pl.DataFrame([mocked_object], table_df_schema)
    table.save()

    assert os.path.exists(file_path)
    printed_text = captured_output.getvalue().strip()

    assert "Just saved df with" in printed_text


def test_all():
    """
    Test multiple table actions in one go
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table(table_name, table_df_schema, ppss)
    table.df = pl.DataFrame([], table_df_schema)
    assert len(table.df) == 0
    table.df = pl.DataFrame([mocked_object], table_df_schema)
    table.load()

    assert len(table.df) == 1


def test_get_pdr_df():
    """
    Test multiple table actions in one go
    """

    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table(table_name, table_df_schema, ppss)

    save_backoff_limit = 5000
    pagination_limit = 1000
    st_timest = 1701634400000
    fin_timest = 1701634400000
    table.get_pdr_df(
        mock_fetch_function,
        "sapphire-mainnet",
        st_timest,
        fin_timest,
        save_backoff_limit,
        pagination_limit,
        {"contract_list": ["0x123"]},
    )
    assert len(table.df) == 1


def test_get_pdr_df_multiple_fetches():
    """
    Test multiple table actions in one go
    """

    st_timestr = "2023-12-03_00:00"
    fin_timestr = "2023-12-03_16:00"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    table = Table("test_prediction_table_multiple", predictions_schema, ppss)
    captured_output = StringIO()
    sys.stdout = captured_output

    save_backoff_limit = 4
    pagination_limit = 2
    st_timest = 1704110400000
    fin_timest = 1704115800000
    table.get_pdr_df(
        fetch_filtered_predictions,
        "sapphire-mainnet",
        st_timest,
        fin_timest,
        save_backoff_limit,
        pagination_limit,
        {"contract_list": ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"]},
    )

    printed_text = captured_output.getvalue().strip()

    # test fetches multiple times
    count_fetches = printed_text.count("Fetched")
    assert count_fetches == 3

    # test saves multiple times
    count_saves = printed_text.count("Saved")
    assert count_saves == 2

    assert len(table.df) == 5
