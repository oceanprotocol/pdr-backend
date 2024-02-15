from io import StringIO
import os
import sys
from polars import Boolean, Float64, Int64, Utf8
import polars as pl
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.table import Table

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

# delete test file if already exists
if os.path.exists(file_path):
    os.remove(file_path)


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

    assert "  Just saved df with" in printed_text


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

    captured_output = StringIO()
    sys.stdout = captured_output

    assert len(table.df) == 0
    table.df = pl.DataFrame([mocked_object], table_df_schema)
    table.load()

    assert len(table.df) == 1
