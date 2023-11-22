import copy
from typing import List, Tuple

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import polars as pl

from pdr_backend.data_eng.constants import TOHLCV_COLS
from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.data_eng.data_factory import DataFactory
from pdr_backend.data_eng.pdutil import (
    initialize_df,
    concat_next_df,
    load_csv,
    load_parquet,
)
from pdr_backend.util.mathutil import has_nan, fill_nans
from pdr_backend.util.timeutil import current_ut, ut_to_timestr

MS_PER_5M_EPOCH = 300000

# ====================================================================
# test parquet updating


def test_update_parquet1(tmpdir):
    _test_update_parquet("2023-01-01_0:00", "2023-01-01_0:00", tmpdir, n_uts=1)


def test_update_parquet2(tmpdir):
    _test_update_parquet("2023-01-01_0:00", "2023-01-01_0:05", tmpdir, n_uts=2)


def test_update_parquet3(tmpdir):
    _test_update_parquet("2023-01-01_0:00", "2023-01-01_0:10", tmpdir, n_uts=3)


def test_update_parquet4(tmpdir):
    _test_update_parquet("2023-01-01_0:00", "2023-01-01_0:45", tmpdir, n_uts=10)


def test_update_parquet5(tmpdir):
    _test_update_parquet("2023-01-01", "2023-06-21", tmpdir, n_uts=">1K")


@enforce_types
def _test_update_parquet(st_timestr: str, fin_timestr: str, tmpdir, n_uts):
    """n_uts -- expected # timestamps. Typically int. If '>1K', expect >1000"""

    # setup: base data
    csvdir = str(tmpdir)

    # setup: uts helpers
    def _calc_ut(since: int, i: int) -> int:
        return since + i * MS_PER_5M_EPOCH

    def _uts_in_range(st_ut: int, fin_ut: int) -> List[int]:
        return [
            _calc_ut(st_ut, i)
            for i in range(100000)  # assume <=100K epochs
            if _calc_ut(st_ut, i) <= fin_ut
        ]

    def _uts_from_since(cur_ut: int, since_ut: int, limit_N: int) -> List[int]:
        return [
            _calc_ut(since_ut, i)
            for i in range(limit_N)
            if _calc_ut(since_ut, i) <= cur_ut
        ]

    # setup: exchange
    class FakeExchange:
        def __init__(self):
            self.cur_ut: int = current_ut()  # fixed value, for easier testing

        # pylint: disable=unused-argument
        def fetch_ohlcv(self, since, limit, *args, **kwargs) -> list:
            uts: List[int] = _uts_from_since(self.cur_ut, since, limit)
            return [[ut] + [1.0] * 5 for ut in uts]  # 1.0 for open, high, ..

    exchange = FakeExchange()

    # setup: pp
    pp = DataPP(  # user-uncontrollable params
        "5m",
        "binanceus h ETH/USDT",
        N_test=2,
    )

    # setup: ss
    ss = DataSS(  # user-controllable params
        ["binanceus h ETH/USDT"],
        csv_dir=csvdir,
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
        max_n_train=7,
        autoregressive_n=3,
    )
    ss.exchs_dict["binanceus"] = exchange  # override with fake exchange

    # setup: data_factory, filename
    data_factory = DataFactory(pp, ss)
    filename = data_factory._hist_parquet_filename("binanceus", "ETH/USDT")

    def _uts_in_parquet(filename: str) -> List[int]:
        df = load_parquet(filename)
        return df["timestamp"].to_list()

    # work 1: new parquet
    data_factory._update_hist_parquet_at_exch_and_pair(
        "binanceus", "ETH/USDT", ss.fin_timestamp
    )
    uts: List[int] = _uts_in_parquet(filename)

    if isinstance(n_uts, int):
        assert len(uts) == n_uts
    elif n_uts == ">1K":
        assert len(uts) > 1000
    assert sorted(uts) == uts
    assert uts[0] == ss.st_timestamp
    assert uts[-1] == ss.fin_timestamp
    assert uts == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)

    # work 2: two more epochs at end --> it'll append existing csv
    ss.fin_timestr = ut_to_timestr(ss.fin_timestamp + 2 * MS_PER_5M_EPOCH)
    data_factory._update_hist_parquet_at_exch_and_pair(
        "binanceus", "ETH/USDT", ss.fin_timestamp
    )
    uts2 = _uts_in_parquet(filename)
    assert uts2 == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)

    # work 3: two more epochs at beginning *and* end --> it'll create new csv
    ss.st_timestr = ut_to_timestr(ss.st_timestamp - 2 * MS_PER_5M_EPOCH)
    ss.fin_timestr = ut_to_timestr(ss.fin_timestamp + 4 * MS_PER_5M_EPOCH)
    data_factory._update_hist_parquet_at_exch_and_pair(
        "binanceus", "ETH/USDT", ss.fin_timestamp
    )
    uts3 = _uts_in_parquet(filename)
    assert uts3 == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)


# # ======================================================================
# # end-to-end tests

# BINANCE_ETH_DATA = [
#     # time          #o   #h  #l    #c    #v
#     [1686805500000, 0.5, 12, 0.12, 1.1, 7.0],
#     [1686805800000, 0.5, 11, 0.11, 2.2, 7.0],
#     [1686806100000, 0.5, 10, 0.10, 3.3, 7.0],
#     [1686806400000, 1.1, 9, 0.09, 4.4, 1.4],
#     [1686806700000, 3.5, 8, 0.08, 5.5, 2.8],
#     [1686807000000, 4.7, 7, 0.07, 6.6, 8.1],
#     [1686807300000, 4.5, 6, 0.06, 7.7, 8.1],
#     [1686807600000, 0.6, 5, 0.05, 8.8, 8.1],
#     [1686807900000, 0.9, 4, 0.04, 9.9, 8.1],
#     [1686808200000, 2.7, 3, 0.03, 10.10, 8.1],
#     [1686808500000, 0.7, 2, 0.02, 11.11, 8.1],
#     [1686808800000, 0.7, 1, 0.01, 12.12, 8.3],
# ]


# @enforce_types
# def _addval(DATA: list, val: float) -> list:
#     DATA2 = copy.deepcopy(DATA)
#     for row_i, row in enumerate(DATA2):
#         for col_j, _ in enumerate(row):
#             if col_j == 0:
#                 continue
#             DATA2[row_i][col_j] += val
#     return DATA2


# BINANCE_BTC_DATA = _addval(BINANCE_ETH_DATA, 10000.0)
# KRAKEN_ETH_DATA = _addval(BINANCE_ETH_DATA, 0.0001)
# KRAKEN_BTC_DATA = _addval(BINANCE_ETH_DATA, 10000.0 + 0.0001)


# @enforce_types
# def test_create_xy__1exchange_1coin_1signal(tmpdir):
#     csvdir = str(tmpdir)

#     csv_dfs = {"kraken": {"ETH-USDT": _df_from_raw_data(BINANCE_ETH_DATA)}}

#     pp, ss = _data_pp_ss_1exchange_1coin_1signal(csvdir)

#     assert ss.n == 1 * 1 * 1 * 3  # n_exchs * n_coins * n_signals * autoregressive_n

#     data_factory = DataFactory(pp, ss)
#     hist_df = data_factory._merge_csv_dfs(csv_dfs)
#     X, y, x_df = data_factory.create_xy(hist_df, testshift=0)
#     _assert_shapes(ss, X, y, x_df)

#     assert X[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
#     assert X[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
#     assert X[0, :].tolist() == [11, 10, 9] and y[0] == 8

#     assert x_df.iloc[-1].tolist() == [4, 3, 2]

#     found_cols = x_df.columns.tolist()
#     target_cols = [
#         "kraken:ETH-USDT:high:t-4",
#         "kraken:ETH-USDT:high:t-3",
#         "kraken:ETH-USDT:high:t-2",
#     ]
#     assert found_cols == target_cols

#     assert x_df["kraken:ETH-USDT:high:t-2"].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]
#     assert X[:, 2].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]

#     # =========== now have a different testshift (1 not 0)
#     X, y, x_df = data_factory.create_xy(hist_df, testshift=1)
#     _assert_shapes(ss, X, y, x_df)

#     assert X[-1, :].tolist() == [5, 4, 3] and y[-1] == 2
#     assert X[-2, :].tolist() == [6, 5, 4] and y[-2] == 3
#     assert X[0, :].tolist() == [12, 11, 10] and y[0] == 9

#     assert x_df.iloc[-1].tolist() == [5, 4, 3]

#     found_cols = x_df.columns.tolist()
#     target_cols = [
#         "kraken:ETH-USDT:high:t-4",
#         "kraken:ETH-USDT:high:t-3",
#         "kraken:ETH-USDT:high:t-2",
#     ]
#     assert found_cols == target_cols

#     assert x_df["kraken:ETH-USDT:high:t-2"].tolist() == [10, 9, 8, 7, 6, 5, 4, 3]
#     assert X[:, 2].tolist() == [10, 9, 8, 7, 6, 5, 4, 3]

#     # =========== now have a different max_n_train
#     ss.max_n_train = 5
#     # ss.autoregressive_n = 2

#     X, y, x_df = data_factory.create_xy(hist_df, testshift=0)
#     _assert_shapes(ss, X, y, x_df)

#     assert X.shape[0] == 5 + 1  # +1 for one test point
#     assert y.shape[0] == 5 + 1
#     assert len(x_df) == 5 + 1

#     assert X[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
#     assert X[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
#     assert X[0, :].tolist() == [9, 8, 7] and y[0] == 6


# @enforce_types
# def test_create_xy__2exchanges_2coins_2signals(tmpdir):
#     csvdir = str(tmpdir)

#     csv_dfs = {
#         "binanceus": {
#             "BTC-USDT": _df_from_raw_data(BINANCE_BTC_DATA),
#             "ETH-USDT": _df_from_raw_data(BINANCE_ETH_DATA),
#         },
#         "kraken": {
#             "BTC-USDT": _df_from_raw_data(KRAKEN_BTC_DATA),
#             "ETH-USDT": _df_from_raw_data(KRAKEN_ETH_DATA),
#         },
#     }

#     pp = DataPP(
#         "5m",
#         "binanceus h ETH/USDT",
#         N_test=2,
#     )

#     ss = DataSS(
#         ["binanceus hl BTC/USDT,ETH/USDT", "kraken hl BTC/USDT,ETH/USDT"],
#         csv_dir=csvdir,
#         st_timestr="2023-06-18",
#         fin_timestr="2023-06-21",
#         max_n_train=7,
#         autoregressive_n=3,
#     )

#     assert ss.n == 2 * 2 * 2 * 3  #  n_exchs * n_coins * n_signals * autoregressive_n

#     data_factory = DataFactory(pp, ss)
#     hist_df = data_factory._merge_csv_dfs(csv_dfs)
#     X, y, x_df = data_factory.create_xy(hist_df, testshift=0)
#     _assert_shapes(ss, X, y, x_df)

#     found_cols = x_df.columns.tolist()
#     target_cols = [
#         "binanceus:BTC-USDT:high:t-4",
#         "binanceus:BTC-USDT:high:t-3",
#         "binanceus:BTC-USDT:high:t-2",
#         "binanceus:ETH-USDT:high:t-4",
#         "binanceus:ETH-USDT:high:t-3",
#         "binanceus:ETH-USDT:high:t-2",
#         "binanceus:BTC-USDT:low:t-4",
#         "binanceus:BTC-USDT:low:t-3",
#         "binanceus:BTC-USDT:low:t-2",
#         "binanceus:ETH-USDT:low:t-4",
#         "binanceus:ETH-USDT:low:t-3",
#         "binanceus:ETH-USDT:low:t-2",
#         "kraken:BTC-USDT:high:t-4",
#         "kraken:BTC-USDT:high:t-3",
#         "kraken:BTC-USDT:high:t-2",
#         "kraken:ETH-USDT:high:t-4",
#         "kraken:ETH-USDT:high:t-3",
#         "kraken:ETH-USDT:high:t-2",
#         "kraken:BTC-USDT:low:t-4",
#         "kraken:BTC-USDT:low:t-3",
#         "kraken:BTC-USDT:low:t-2",
#         "kraken:ETH-USDT:low:t-4",
#         "kraken:ETH-USDT:low:t-3",
#         "kraken:ETH-USDT:low:t-2",
#     ]
#     assert found_cols == target_cols

#     # test binanceus:ETH-USDT:high like in 1-signal
#     assert target_cols[3:6] == [
#         "binanceus:ETH-USDT:high:t-4",
#         "binanceus:ETH-USDT:high:t-3",
#         "binanceus:ETH-USDT:high:t-2",
#     ]
#     Xa = X[:, 3:6]
#     assert Xa[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
#     assert Xa[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
#     assert Xa[0, :].tolist() == [11, 10, 9] and y[0] == 8

#     assert x_df.iloc[-1].tolist()[3:6] == [4, 3, 2]
#     assert x_df.iloc[-2].tolist()[3:6] == [5, 4, 3]
#     assert x_df.iloc[0].tolist()[3:6] == [11, 10, 9]

#     assert x_df["binanceus:ETH-USDT:high:t-2"].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]
#     assert Xa[:, 2].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]


# @enforce_types
# def test_create_xy__handle_nan(tmpdir):
#     # create hist_df
#     csvdir = str(tmpdir)
#     csv_dfs = {"kraken": {"ETH-USDT": _df_from_raw_data(BINANCE_ETH_DATA)}}
#     pp, ss = _data_pp_ss_1exchange_1coin_1signal(csvdir)
#     data_factory = DataFactory(pp, ss)
#     hist_df = data_factory._merge_csv_dfs(csv_dfs)

#     # corrupt hist_df with nans
#     all_signal_strs = set(signal_str for _, signal_str, _ in ss.input_feed_tups)
#     assert "high" in all_signal_strs
#     hist_df.at[1686805800000, "kraken:ETH-USDT:high"] = np.nan  # first row
#     hist_df.at[1686806700000, "kraken:ETH-USDT:high"] = np.nan  # middle row
#     hist_df.at[1686808800000, "kraken:ETH-USDT:high"] = np.nan  # last row
#     assert has_nan(hist_df)

#     # run create_xy() and force the nans to stick around
#     # -> we want to ensure that we're building X/y with risk of nan
#     X, y, x_df = data_factory.create_xy(hist_df, testshift=0, do_fill_nans=False)
#     assert has_nan(X) and has_nan(y) and has_nan(x_df)

#     # nan approach 1: fix externally
#     hist_df2 = fill_nans(hist_df)
#     assert not has_nan(hist_df2)

#     # nan approach 2: explicitly tell create_xy to fill nans
#     X, y, x_df = data_factory.create_xy(hist_df, testshift=0, do_fill_nans=True)
#     assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)

#     # nan approach 3: create_xy fills nans by default (best)
#     X, y, x_df = data_factory.create_xy(hist_df, testshift=0)
#     assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)


# @enforce_types
# def _data_pp_ss_1exchange_1coin_1signal(csvdir: str) -> Tuple[DataPP, DataSS]:
#     pp = DataPP(
#         "5m",
#         "kraken h ETH/USDT",
#         N_test=2,
#     )

#     ss = DataSS(
#         [pp.predict_feed_str],
#         csv_dir=csvdir,
#         st_timestr="2023-06-18",
#         fin_timestr="2023-06-21",
#         max_n_train=7,
#         autoregressive_n=3,
#     )
#     return pp, ss


# @enforce_types
# def _assert_shapes(ss: DataSS, X: np.ndarray, y: np.ndarray, x_df: pd.DataFrame):
#     assert X.shape[0] == y.shape[0]
#     assert X.shape[0] == (ss.max_n_train + 1)  # 1 for test, rest for train
#     assert X.shape[1] == ss.n

#     assert len(x_df) == X.shape[0]
#     assert len(x_df.columns) == ss.n


# @enforce_types
# def _df_from_raw_data(raw_data: list) -> pd.DataFrame:
#     df = initialize_df(TOHLCV_COLS)
#     next_df = pd.DataFrame(raw_data, columns=TOHLCV_COLS)
#     df = concat_next_df(df, next_df)
#     return df
