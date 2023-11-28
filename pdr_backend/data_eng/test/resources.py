import copy

from enforce_typing import enforce_types
import polars as pl


from pdr_backend.data_eng.constants import TOHLCV_COLS, TOHLCV_SCHEMA_PL
from pdr_backend.data_eng.model_data_factory import ModelDataFactory
from pdr_backend.data_eng.parquet_data_factory import ParquetDataFactory
from pdr_backend.data_eng.plutil import (
    concat_next_df,
    initialize_df,
    transform_df,
)
from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS


@enforce_types
def _data_pp_ss_1feed(tmpdir, feed, st_timestr=None, fin_timestr=None):
    parquet_dir = str(tmpdir)
    pp = _data_pp([feed])
    ss = _data_ss(parquet_dir, [feed], st_timestr, fin_timestr)
    pq_data_factory = ParquetDataFactory(pp, ss)
    model_data_factory = ModelDataFactory(pp, ss)
    return pp, ss, pq_data_factory, model_data_factory


@enforce_types
def _data_pp(predict_feeds) -> DataPP:
    return DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": predict_feeds,
            "sim_only": {"test_n": 2},
        }
    )


@enforce_types
def _data_ss(parquet_dir, input_feeds, st_timestr=None, fin_timestr=None):
    return DataSS(
        {
            "input_feeds": input_feeds,
            "parquet_dir": parquet_dir,
            "st_timestr": st_timestr or "2023-06-18",
            "fin_timestr": fin_timestr or "2023-06-21",
            "max_n_train": 7,
            "autoregressive_n": 3,
        }
    )


@enforce_types
def _df_from_raw_data(raw_data: list) -> pl.DataFrame:
    """Return a df for use in parquet_dfs"""
    df = initialize_df(TOHLCV_COLS)

    next_df = pl.DataFrame(raw_data, schema=TOHLCV_SCHEMA_PL)

    df = concat_next_df(df, next_df)
    df = transform_df(df)

    return df


BINANCE_ETH_DATA = [
    # time          #o   #h  #l    #c    #v
    [1686805500000, 0.5, 12, 0.12, 1.1, 7.0],
    [1686805800000, 0.5, 11, 0.11, 2.2, 7.0],
    [1686806100000, 0.5, 10, 0.10, 3.3, 7.0],
    [1686806400000, 1.1, 9, 0.09, 4.4, 1.4],
    [1686806700000, 3.5, 8, 0.08, 5.5, 2.8],
    [1686807000000, 4.7, 7, 0.07, 6.6, 8.1],
    [1686807300000, 4.5, 6, 0.06, 7.7, 8.1],
    [1686807600000, 0.6, 5, 0.05, 8.8, 8.1],
    [1686807900000, 0.9, 4, 0.04, 9.9, 8.1],
    [1686808200000, 2.7, 3, 0.03, 10.10, 8.1],
    [1686808500000, 0.7, 2, 0.02, 11.11, 8.1],
    [1686808800000, 0.7, 1, 0.01, 12.12, 8.3],
]


@enforce_types
def _addval(DATA: list, val: float) -> list:
    DATA2 = copy.deepcopy(DATA)
    for row_i, row in enumerate(DATA2):
        for col_j, _ in enumerate(row):
            if col_j == 0:
                continue
            DATA2[row_i][col_j] += val
    return DATA2


BINANCE_BTC_DATA = _addval(BINANCE_ETH_DATA, 10000.0)
KRAKEN_ETH_DATA = _addval(BINANCE_ETH_DATA, 0.0001)
KRAKEN_BTC_DATA = _addval(BINANCE_ETH_DATA, 10000.0 + 0.0001)

ETHUSDT_PARQUET_DFS = {
    "binanceus": {
        "ETH-USDT": _df_from_raw_data(BINANCE_ETH_DATA),
    }
}
