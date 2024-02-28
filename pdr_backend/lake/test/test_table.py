from io import StringIO
import os
import sys
from polars import Boolean, Float64, Int64, Utf8
import polars as pl
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.table import Table
from pdr_backend.subgraph.subgraph_predictions import fetch_filtered_predictions
from pdr_backend.lake.table_pdr_predictions import predictions_schema
from pdr_backend.util.time_types import UnixTimeMs


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
    "timestamp": 1701634400,
    "slot": 1701634400,
    "user": "0x123",
}

def _clean_up(tmp_path, table_name):
    """
    Delete test file if already exists
    """
    folder_path = os.path.join(tmp_path, table_name)
    
    if os.path.exists(folder_path):
        #delete files
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            os.remove(file_path)
        os.remove(folder_path)


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

def test_save_table(tmpdir):
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    _clean_up(ppss.lake_ss.parquet_dir, table_name)

    table = Table(table_name, table_df_schema, ppss)

    captured_output = StringIO()
    sys.stdout = captured_output

    assert len(table.df) == 0
    table.df = pl.DataFrame([mocked_object], table_df_schema)
    table.save()

    first_ts = table.df.head(1)["timestamp"].to_list()[0]
    last_ts = table.df.tail(1)["timestamp"].to_list()[0]

    test_file_path = os.path.join(str(ppss.lake_ss.parquet_dir), table_name, f"{table_name}_from_{first_ts}_to_{last_ts}_{len(table.df)}.csv")
    assert os.path.exists(test_file_path)
    printed_text = captured_output.getvalue().strip()

    assert "Just saved df with" in printed_text

def test_get_pdr_df(tmpdir):
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    _clean_up(ppss.lake_ss.parquet_dir, table_name)

    table = Table(table_name, table_df_schema, ppss)

    save_backoff_limit = 5000
    pagination_limit = 1000
    st_timest = UnixTimeMs(1701634300000)
    fin_timest = UnixTimeMs(1701634500000)
    table.get_pdr_df(
        mock_fetch_function,
        "sapphire-mainnet",
        st_timest,
        fin_timest,
        save_backoff_limit,
        pagination_limit,
        {"contract_list": ["0x123"]},
    )

    assert table.df.shape[0] == 1

def test_get_pdr_df_multiple_fetches(tmpdir):
    """
    Test multiple table actions in one go
    """

    st_timestr = "2023-12-03_00:00"
    fin_timestr = "2023-12-03_16:00"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    _clean_up(ppss.lake_ss.parquet_dir, table_name)

    table = Table("test_prediction_table_multiple", predictions_schema, ppss)
    captured_output = StringIO()
    sys.stdout = captured_output

    save_backoff_limit = 40
    pagination_limit = 20
    st_timest = UnixTimeMs(1704110400000)
    fin_timest = UnixTimeMs(1704111600000)
    table.get_pdr_df(
        fetch_function=fetch_filtered_predictions,
        network="sapphire-mainnet",
        st_ut=st_timest,
        fin_ut=fin_timest,
        save_backoff_limit=save_backoff_limit,
        pagination_limit=pagination_limit,
        config={"contract_list": ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"]},
    )
    printed_text = captured_output.getvalue().strip()

    # test fetches multiple times
    count_fetches = printed_text.count("Fetched")
    assert count_fetches == 3

    # test saves multiple times
    count_saves = printed_text.count("Saved")
    assert count_saves == 2

    # test that the final df is saved
    assert len(table.df) == 50

def test_all(tmpdir):
    """
    Test multiple table actions in one go
    """
    st_timestr = "2021-12-03"
    fin_timestr = "2023-12-31"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    _clean_up(ppss.lake_ss.parquet_dir, table_name)

    folder_path = os.path.join(ppss.lake_ss.parquet_dir, table_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    #create the csv file
    file_path = os.path.join(folder_path, f"{table_name}_from_1701634400_to_1701634400_1.csv")

    #write the file
    with open(file_path, "w") as file:
        file.write("ID,pair,timeframe,prediction,payout,timestamp,slot,user\n")
        file.write("0x123,ADA-USDT,5m,True,28.2,1701634400000,1701634400000,0x123\n")

    table = Table(table_name, table_df_schema, ppss)
    table.df = pl.DataFrame([], table_df_schema)
    assert len(table.df) == 0

    table.load()
    assert len(table.df) == 1
