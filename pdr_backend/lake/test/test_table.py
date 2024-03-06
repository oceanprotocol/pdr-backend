from io import StringIO
import os
import sys

from polars import Boolean, Float64, Int64, Utf8
import polars as pl
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.table import Table
# from pdr_backend.subgraph.prediction import (
#     Prediction
# )
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema, 
    predictions_table_name
)
from pdr_backend.util.time_types import UnixTimeMs


# def _clean_up(tmp_path):
#     """
#     Delete test file if already exists
#     """
#     folder_path = os.path.join(tmp_path, table_name)

#     if os.path.exists(folder_path):
#         # delete files
#         for file in os.listdir(folder_path):
#             file_path = os.path.join(folder_path, file)
#             os.remove(file_path)
#         os.remove(folder_path)


# def write_mock_csv_file(
#         folder_path:str, 
#         file_name:str, 
#         st_ts: UnixTimeS, 
#         end_ts: UnixTimeS, 
#         header: str, 
#         data: str):
    
#     """
#     @description
#         Write data to a csv file
#     """
#     _clean_up(folder_path)

#     folder_path = os.path.join(folder_path, file_name)
#     if not os.path.exists(folder_path):
#         os.makedirs(folder_path)

#     # create the csv file
#     file_path = os.path.join(
#         folder_path, f"{table_name}_from_{st_ts}_to_{end_ts}.csv"
#     )

#     # write the file
#     with open(file_path, "w") as file:
#         file.write(header)
#         file.write(data)

#     return file_path


# mock_header = "ID,pair,timeframe,prediction,payout,timestamp,slot,user\n"
# mock_data = "0x123,ADA-USDT,5m,True,28.2,1701634400000,1701634400000,0x123\n"


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

    table = Table(predictions_table_name, predictions_schema, ppss)

    assert table.table_name == predictions_table_name
    assert table.ppss.lake_ss.st_timestr == st_timestr
    assert table.ppss.lake_ss.fin_timestr == fin_timestr

    df = table.persistent_data_store.query_data(
        predictions_table_name, 
        f"SELECT * FROM {predictions_table_name}"
    )
    assert len(df) == 0


# def test_load_table():
#     """
#     Test that table is loading the data from file
#     """
#     st_timestr = "2023-12-03"
#     fin_timestr = "2024-12-05"
#     ppss = mock_ppss(
#         ["binance BTC/USDT c 5m"],
#         "sapphire-mainnet",
#         ".",
#         st_timestr=st_timestr,
#         fin_timestr=fin_timestr,
#     )

#     table = Table(table_name, table_df_schema, ppss)
    

# def test_all(tmpdir):
#     """
#     Test multiple table actions in one go
#     """
#     st_timestr = "2021-12-03"
#     fin_timestr = "2023-12-31"
#     ppss = mock_ppss(
#         ["binance BTC/USDT c 5m"],
#         "sapphire-mainnet",
#         str(tmpdir),
#         st_timestr=st_timestr,
#         fin_timestr=fin_timestr,
#     )

    

#     table = Table(table_name, table_df_schema, ppss)
#     # query table and assert length
#     # assert len(table.df) == 0
    
#     # append to table
#     # query table and assert length
#     # assert len(table.df) == 1


# def test_append_to_db(tmpdir):
#     """
#     Test that table is loading the data from file
#     """
#     st_timestr = "2023-12-03"
#     fin_timestr = "2024-12-05"
#     ppss = mock_ppss(
#         ["binance BTC/USDT c 5m"],
#         "sapphire-mainnet",
#         str(tmpdir),
#         st_timestr=st_timestr,
#         fin_timestr=fin_timestr,
#     )

#     _clean_up(ppss.lake_ss.parquet_dir)

#     table = Table(table_name, table_df_schema, ppss)
    
#     # query table and assert length
#     # assert len(table.df) == 0

#     table._append_to_db(pl.DataFrame([mocked_object] * 1000, schema=table_df_schema))

#     result = table.persistent_data_store.query_data(
#         table.table_name, "SELECT * FROM {view_name}"
#     )

#     assert result["ID"][0] == "0x123"
#     assert result["pair"][0] == "ADA-USDT"
#     assert result["timeframe"][0] == "5m"
#     assert result["predvalue"][0] is True
#     assert len(result) == 1000


# def test_append_to_csv(tmpdir):
#     """
#     Test that table is loading the data from file
#     """
#     st_timestr = "2023-12-03"
#     fin_timestr = "2024-12-05"
#     ppss = mock_ppss(
#         ["binance BTC/USDT c 5m"],
#         "sapphire-mainnet",
#         str(tmpdir),
#         st_timestr=st_timestr,
#         fin_timestr=fin_timestr,
#     )

#     _clean_up(ppss.lake_ss.parquet_dir)

#     table = Table(table_name, table_df_schema, ppss)
#     # query table and assert length
#     # assert len(table.df) == 0

#     table._append_to_csv(pl.DataFrame([mocked_object] * 1000, schema=table_df_schema))

#     file_path = os.path.join(
#         ppss.lake_ss.parquet_dir,
#         table_name,
#         f"{table_name}_from_1701634400_to_1701634400.csv",
#     )

#     assert os.path.exists(file_path)

#     with open(file_path, "r") as file:
#         lines = file.readlines()
#         assert len(lines) == 1001
