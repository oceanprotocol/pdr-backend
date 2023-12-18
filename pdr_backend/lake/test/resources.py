import copy

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.constants import TOHLCV_COLS, TOHLCV_SCHEMA_PL
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.merge_df import merge_rawohlcv_dfs
from pdr_backend.lake.plutil import text_to_df
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.lake.plutil import (
    concat_next_df,
    initialize_rawohlcv_df,
    transform_df,
)
from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import mock_web3_pp


@enforce_types
def _mergedohlcv_df_ETHUSDT(tmpdir):
    _, _, _, aimodel_data_factory = _data_pp_ss_1feed(tmpdir, "binanceus h ETH/USDT")
    mergedohlcv_df = merge_rawohlcv_dfs(ETHUSDT_RAWOHLCV_DFS)
    return mergedohlcv_df, aimodel_data_factory


@enforce_types
def _data_pp_ss_1feed(tmpdir, feed, st_timestr=None, fin_timestr=None):
    parquet_dir = str(tmpdir)
    pp = _data_pp([feed])
    ss = _data_ss(parquet_dir, [feed], st_timestr, fin_timestr)
    ohlcv_data_factory = OhlcvDataFactory(pp, ss)
    aimodel_data_factory = AimodelDataFactory(pp, ss)
    return pp, ss, ohlcv_data_factory, aimodel_data_factory


@enforce_types
def _gql_data_factory(tmpdir, feed, st_timestr=None, fin_timestr=None):
    network = "sapphire-mainnet"
    ppss = mock_ppss("5m", [feed], network, str(tmpdir), st_timestr, fin_timestr)
    ppss.web3_pp = mock_web3_pp(network)
    gql_data_factory = GQLDataFactory(ppss)
    return ppss, gql_data_factory


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


# ==================================================================


@enforce_types
def _df_from_raw_data(raw_data: list) -> pl.DataFrame:
    """Return a df for use in rawohlcv_dfs"""
    df = initialize_rawohlcv_df(TOHLCV_COLS)

    next_df = pl.DataFrame(raw_data, schema=TOHLCV_SCHEMA_PL)

    df = concat_next_df(df, next_df)
    df = transform_df(df)

    return df


BINANCE_ETH_DATA = [  # oldest first, newest on the bottom (at the end)
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

ETHUSDT_RAWOHLCV_DFS = {
    "binanceus": {
        "ETH/USDT": _df_from_raw_data(BINANCE_ETH_DATA),
    }
}

# ==================================================================

RAW_DF1 = text_to_df(  # binance BTC/USDT
    """datetime|timestamp|open|close
d0|0|10.0|11.0
d1|1|10.1|11.1
d3|3|10.3|11.3
d4|4|10.4|11.4
"""
)  # does not have: "d2|2|10.2|11.2" to simulate missing vals from exchanges

RAW_DF2 = text_to_df(  # binance ETH/USDT
    """datetime|timestamp|open|close
d0|0|20.0|21.0
d1|1|20.1|21.1
d2|2|20.2|21.2
d3|3|20.3|21.3
"""
)  # does *not* have: "d4|4|20.4|21.4" to simulate missing vals from exchanges

RAW_DF3 = text_to_df(  # kraken BTC/USDT
    """datetime|timestamp|open|close
d0|0|30.0|31.0
d1|1|30.1|31.1
d2|2|30.2|31.2
d3|3|30.3|31.3
d4|4|30.4|31.4
"""
)

RAW_DF4 = text_to_df(  # kraken ETH/USDT
    """datetime|timestamp|open|close
d0|0|40.0|41.0
d1|1|40.1|41.1
d2|2|40.2|41.2
d3|3|40.3|41.3
d4|4|40.4|41.4
"""
)
