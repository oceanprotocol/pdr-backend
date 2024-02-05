import copy
from typing import Dict

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.lake.constants import TOHLCV_COLS, TOHLCV_SCHEMA_PL
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.merge_df import merge_rawohlcv_dfs
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.lake.plutil import concat_next_df, initialize_rawohlcv_df, text_to_df
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import mock_web3_pp


@enforce_types
def _mergedohlcv_df_ETHUSDT(tmpdir):
    _, _, aimodel_data_factory = _predictoor_ss_1feed(tmpdir, "binanceus ETH/USDT h 5m")
    mergedohlcv_df = merge_rawohlcv_dfs(ETHUSDT_RAWOHLCV_DFS)
    return mergedohlcv_df, aimodel_data_factory


@enforce_types
def _predictoor_ss_1feed(tmpdir, feed):
    predictoor_ss = _predictoor_ss(feed, [feed])
    lake_ss = _lake_ss(tmpdir, [feed])
    ohlcv_data_factory = OhlcvDataFactory(lake_ss)
    aimodel_data_factory = AimodelDataFactory(predictoor_ss)
    return predictoor_ss, ohlcv_data_factory, aimodel_data_factory


@enforce_types
def _lake_ss_1feed(tmpdir, feed, st_timestr=None, fin_timestr=None):
    parquet_dir = str(tmpdir)
    ss = _lake_ss(parquet_dir, [feed], st_timestr, fin_timestr)
    ohlcv_data_factory = OhlcvDataFactory(ss)
    return ss, ohlcv_data_factory


@enforce_types
def _gql_data_factory(tmpdir, feed, st_timestr=None, fin_timestr=None):
    network = "sapphire-mainnet"
    ppss = mock_ppss([feed], network, str(tmpdir), st_timestr, fin_timestr)
    ppss.web3_pp = mock_web3_pp(network)

    # setup lake
    parquet_dir = str(tmpdir)
    lake_ss = _lake_ss(parquet_dir, [feed], st_timestr, fin_timestr)
    ppss.lake_ss = lake_ss

    gql_data_factory = GQLDataFactory(ppss)
    return ppss, gql_data_factory


def _filter_gql_tables_config(record_config: Dict, record_filter: str) -> Dict:
    # Return a filtered version of record_config for testing
    print({k: v for k, v in record_config["tables"].items() if k == record_filter})
    return {k: v for k, v in record_config["tables"].items() if k == record_filter}


@enforce_types
def _predictoor_ss(feed, feeds):
    return PredictoorSS(
        {
            "predict_feed": feed,
            "timeframe": "5m",
            "bot_only": {"s_until_epoch_end": 60, "stake_amount": 1},
            "aimodel_ss": {
                "input_feeds": feeds,
                "approach": "LIN",
                "max_n_train": 7,
                "autoregressive_n": 3,
            },
        }
    )


@enforce_types
def _lake_ss(parquet_dir, feeds, st_timestr=None, fin_timestr=None):
    return LakeSS(
        {
            "feeds": feeds,
            "parquet_dir": parquet_dir,
            "st_timestr": st_timestr or "2023-06-18",
            "fin_timestr": fin_timestr or "2023-06-21",
            "timeframe": "5m",
        }
    )


# ==================================================================


@enforce_types
def _df_from_raw_data(raw_data: list) -> pl.DataFrame:
    """Return a df for use in rawohlcv_dfs"""
    df = initialize_rawohlcv_df(TOHLCV_COLS)

    next_df = pl.DataFrame(raw_data, schema=TOHLCV_SCHEMA_PL)

    df = concat_next_df(df, next_df)

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
    """timestamp|open|close
0|10.0|11.0
1|10.1|11.1
3|10.3|11.3
4|10.4|11.4
"""
)  # does not have: "2|10.2|11.2" to simulate missing vals from exchanges

RAW_DF2 = text_to_df(  # binance ETH/USDT
    """timestamp|open|close
0|20.0|21.0
1|20.1|21.1
2|20.2|21.2
3|20.3|21.3
"""
)  # does *not* have: "4|20.4|21.4" to simulate missing vals from exchanges

RAW_DF3 = text_to_df(  # kraken BTC/USDT
    """timestamp|open|close
0|30.0|31.0
1|30.1|31.1
2|30.2|31.2
3|30.3|31.3
4|30.4|31.4
"""
)

RAW_DF4 = text_to_df(  # kraken ETH/USDT
    """timestamp|open|close
0|40.0|41.0
1|40.1|41.1
2|40.2|41.2
3|40.3|41.3
4|40.4|41.4
"""
)
