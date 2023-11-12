import copy
from typing import Tuple

from enforce_typing import enforce_types
import numpy as np
import pandas as pd

from pdr_backend.data_eng.constants import TOHLCV_COLS
from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.data_eng.data_factory import DataFactory
from pdr_backend.data_eng.pdutil import (
    initialize_df,
    concat_next_df,
    load_csv,
)
from pdr_backend.util.mathutil import has_nan, fill_nans
from pdr_backend.util.timeutil import (
    current_ut,
    timestr_to_ut,
)

MS_PER_5M_EPOCH = 300000

# ====================================================================
# test csv updating


def test_update_csv1(tmpdir):
    _test_update_csv("2023-01-01_0:00", "2023-01-01_0:00", tmpdir, n_uts=1)


def test_update_csv2(tmpdir):
    _test_update_csv("2023-01-01_0:00", "2023-01-01_0:05", tmpdir, n_uts=2)


def test_update_csv3(tmpdir):
    _test_update_csv("2023-01-01_0:00", "2023-01-01_0:10", tmpdir, n_uts=3)


def test_update_csv4(tmpdir):
    _test_update_csv("2023-01-01_0:00", "2023-01-01_0:45", tmpdir, n_uts=10)


def test_update_csv5(tmpdir):
    _test_update_csv("2023-01-01", "2023-06-21", tmpdir, n_uts=">1K")


@enforce_types
def _test_update_csv(st_str: str, fin_str: str, tmpdir, n_uts):
    """n_uts -- expected # timestamps. Typically int. If '>1K', expect >1000"""

    # setup: base data
    st_ut = timestr_to_ut(st_str)
    fin_ut = timestr_to_ut(fin_str)
    csvdir = str(tmpdir)

    # setup: uts helpers
    def _calc_ut(since: int, i: int) -> int:
        return since + i * MS_PER_5M_EPOCH

    def _uts_in_range(st_ut, fin_ut):
        return [
            _calc_ut(st_ut, i)
            for i in range(100000)  # assume <=100K epochs
            if _calc_ut(st_ut, i) <= fin_ut
        ]

    def _uts_from_since(cur_ut, since, limit_N):
        return [
            _calc_ut(since, i) for i in range(limit_N) if _calc_ut(since, i) <= cur_ut
        ]

    # setup: exchange
    class FakeExchange:
        def __init__(self):
            self.cur_ut = current_ut()  # fixed value, for easier testing

        # pylint: disable=unused-argument
        def fetch_ohlcv(self, since, limit, *args, **kwargs) -> list:
            uts = _uts_from_since(self.cur_ut, since, limit)
            return [[ut] + [1.0] * 5 for ut in uts]  # 1.0 for open, high, ..

    exchange = FakeExchange()

    # setup: pp
    pp = DataPP(  # user-uncontrollable params
        timeframe="5m",
        yval_exchange_id="binanceus",
        yval_coin="ETH",
        usdcoin="USDT",
        yval_signal="high",
        N_test=2,
    )

    # setup: ss
    ss = DataSS(  # user-controllable params
        csv_dir=csvdir,
        st_timestamp=st_ut,
        fin_timestamp=fin_ut,
        max_N_train=7,
        Nt=3,
        signals=["high"],
        coins=["ETH"],
        exchange_ids=["binanceus"],
    )
    ss.exchs_dict["binanceus"] = exchange

    # setup: data_factory, filename
    data_factory = DataFactory(pp, ss)
    filename = data_factory._hist_csv_filename("binanceus", "ETH/USDT")

    def _uts_in_csv(filename: str) -> list:
        df = load_csv(filename)
        return df.index.values.tolist()

    # work 1: new csv
    data_factory._update_hist_csv_at_exch_and_pair("binanceus", "ETH/USDT")
    uts = _uts_in_csv(filename)
    if isinstance(n_uts, int):
        assert len(uts) == n_uts
    elif n_uts == ">1K":
        assert len(uts) > 1000
    assert sorted(uts) == uts and uts[0] == st_ut and uts[-1] == fin_ut
    assert uts == _uts_in_range(st_ut, fin_ut)

    # work 2: two more epochs at end --> it'll append existing csv
    ss.fin_timestamp = fin_ut + 2 * MS_PER_5M_EPOCH
    data_factory._update_hist_csv_at_exch_and_pair("binanceus", "ETH/USDT")
    uts2 = _uts_in_csv(filename)
    assert uts2 == _uts_in_range(st_ut, fin_ut + 2 * MS_PER_5M_EPOCH)

    # work 3: two more epochs at beginning *and* end --> it'll create new csv
    ss.st_timestamp = st_ut - 2 * MS_PER_5M_EPOCH
    ss.fin_timestamp = fin_ut + 4 * MS_PER_5M_EPOCH
    data_factory._update_hist_csv_at_exch_and_pair("binanceus", "ETH/USDT")
    uts3 = _uts_in_csv(filename)
    assert uts3 == _uts_in_range(
        st_ut - 2 * MS_PER_5M_EPOCH, fin_ut + 4 * MS_PER_5M_EPOCH
    )


# ======================================================================
# end-to-end tests

BINANCE_ETH_DATA = [
    # time           #open  #high  #low    #close  #volume
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


@enforce_types
def test_create_xy__1exchange_1coin_1signal(tmpdir):
    csvdir = str(tmpdir)

    csv_dfs = {"kraken": {"ETH": _df_from_raw_data(BINANCE_ETH_DATA)}}

    pp, ss = _data_pp_ss_1exchange_1coin_1signal(csvdir)

    assert ss.n == 1 * 1 * 1 * 3  # n_exchs * n_coins * n_signals * Nt

    data_factory = DataFactory(pp, ss)
    hist_df = data_factory._merge_csv_dfs(csv_dfs)
    X, y, x_df = data_factory.create_xy(hist_df, testshift=0)
    _assert_shapes(ss, X, y, x_df)

    assert X[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
    assert X[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
    assert X[0, :].tolist() == [11, 10, 9] and y[0] == 8

    assert x_df.iloc[-1].tolist() == [4, 3, 2]

    found_cols = x_df.columns.tolist()
    target_cols = [
        "kraken:ETH:high:t-4",
        "kraken:ETH:high:t-3",
        "kraken:ETH:high:t-2",
    ]
    assert found_cols == target_cols

    assert x_df["kraken:ETH:high:t-2"].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]
    assert X[:, 2].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]

    # =========== now have a different testshift (1 not 0)
    X, y, x_df = data_factory.create_xy(hist_df, testshift=1)
    _assert_shapes(ss, X, y, x_df)

    assert X[-1, :].tolist() == [5, 4, 3] and y[-1] == 2
    assert X[-2, :].tolist() == [6, 5, 4] and y[-2] == 3
    assert X[0, :].tolist() == [12, 11, 10] and y[0] == 9

    assert x_df.iloc[-1].tolist() == [5, 4, 3]

    found_cols = x_df.columns.tolist()
    target_cols = [
        "kraken:ETH:high:t-4",
        "kraken:ETH:high:t-3",
        "kraken:ETH:high:t-2",
    ]
    assert found_cols == target_cols

    assert x_df["kraken:ETH:high:t-2"].tolist() == [10, 9, 8, 7, 6, 5, 4, 3]
    assert X[:, 2].tolist() == [10, 9, 8, 7, 6, 5, 4, 3]

    # =========== now have a different max_N_train
    ss.max_N_train = 5
    # ss.Nt = 2

    X, y, x_df = data_factory.create_xy(hist_df, testshift=0)
    _assert_shapes(ss, X, y, x_df)

    assert X.shape[0] == 5 + 1  # +1 for one test point
    assert y.shape[0] == 5 + 1
    assert len(x_df) == 5 + 1

    assert X[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
    assert X[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
    assert X[0, :].tolist() == [9, 8, 7] and y[0] == 6


@enforce_types
def test_create_xy__2exchanges_2coins_2signals(tmpdir):
    csvdir = str(tmpdir)

    csv_dfs = {
        "binanceus": {
            "BTC": _df_from_raw_data(BINANCE_BTC_DATA),
            "ETH": _df_from_raw_data(BINANCE_ETH_DATA),
        },
        "kraken": {
            "BTC": _df_from_raw_data(KRAKEN_BTC_DATA),
            "ETH": _df_from_raw_data(KRAKEN_ETH_DATA),
        },
    }

    pp = DataPP(
        timeframe="5m",
        yval_exchange_id="binanceus",
        yval_coin="ETH",
        usdcoin="USDT",
        yval_signal="high",
        N_test=2,
    )

    ss = DataSS(
        csv_dir=csvdir,
        st_timestamp=timestr_to_ut("2023-06-18"),
        fin_timestamp=timestr_to_ut("2023-06-21"),
        max_N_train=7,
        Nt=3,
        signals=["high", "low"],
        coins=["BTC", "ETH"],
        exchange_ids=["binanceus", "kraken"],
    )

    assert ss.n == 2 * 2 * 2 * 3  #  n_exchs * n_coins * n_signals * Nt

    data_factory = DataFactory(pp, ss)
    hist_df = data_factory._merge_csv_dfs(csv_dfs)
    X, y, x_df = data_factory.create_xy(hist_df, testshift=0)
    _assert_shapes(ss, X, y, x_df)

    found_cols = x_df.columns.tolist()
    target_cols = [
        "binanceus:BTC:high:t-4",
        "binanceus:BTC:high:t-3",
        "binanceus:BTC:high:t-2",
        "binanceus:BTC:low:t-4",
        "binanceus:BTC:low:t-3",
        "binanceus:BTC:low:t-2",
        "binanceus:ETH:high:t-4",
        "binanceus:ETH:high:t-3",
        "binanceus:ETH:high:t-2",
        "binanceus:ETH:low:t-4",
        "binanceus:ETH:low:t-3",
        "binanceus:ETH:low:t-2",
        "kraken:BTC:high:t-4",
        "kraken:BTC:high:t-3",
        "kraken:BTC:high:t-2",
        "kraken:BTC:low:t-4",
        "kraken:BTC:low:t-3",
        "kraken:BTC:low:t-2",
        "kraken:ETH:high:t-4",
        "kraken:ETH:high:t-3",
        "kraken:ETH:high:t-2",
        "kraken:ETH:low:t-4",
        "kraken:ETH:low:t-3",
        "kraken:ETH:low:t-2",
    ]
    assert found_cols == target_cols

    # test binanceus:ETH:high like in 1-signal
    assert target_cols[6:9] == [
        "binanceus:ETH:high:t-4",
        "binanceus:ETH:high:t-3",
        "binanceus:ETH:high:t-2",
    ]
    Xa = X[:, 6:9]
    assert Xa[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
    assert Xa[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
    assert Xa[0, :].tolist() == [11, 10, 9] and y[0] == 8

    assert x_df.iloc[-1].tolist()[6:9] == [4, 3, 2]
    assert x_df.iloc[-2].tolist()[6:9] == [5, 4, 3]
    assert x_df.iloc[0].tolist()[6:9] == [11, 10, 9]

    assert x_df["binanceus:ETH:high:t-2"].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]
    assert Xa[:, 2].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]


@enforce_types
def test_create_xy__handle_nan(tmpdir):
    # create hist_df
    csvdir = str(tmpdir)
    csv_dfs = {"kraken": {"ETH": _df_from_raw_data(BINANCE_ETH_DATA)}}
    pp, ss = _data_pp_ss_1exchange_1coin_1signal(csvdir)
    data_factory = DataFactory(pp, ss)
    hist_df = data_factory._merge_csv_dfs(csv_dfs)

    # corrupt hist_df with nans
    assert "high" in ss.signals
    hist_df.at[1686805800000, "kraken:ETH:high"] = np.nan  # first row
    hist_df.at[1686806700000, "kraken:ETH:high"] = np.nan  # middle row
    hist_df.at[1686808800000, "kraken:ETH:high"] = np.nan  # last row
    assert has_nan(hist_df)

    # run create_xy() and force the nans to stick around
    # -> we want to ensure that we're building X/y with risk of nan
    X, y, x_df = data_factory.create_xy(hist_df, testshift=0, do_fill_nans=False)
    assert has_nan(X) and has_nan(y) and has_nan(x_df)

    # nan approach 1: fix externally
    hist_df2 = fill_nans(hist_df)
    assert not has_nan(hist_df2)

    # nan approach 2: explicitly tell create_xy to fill nans
    X, y, x_df = data_factory.create_xy(hist_df, testshift=0, do_fill_nans=True)
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)

    # nan approach 3: create_xy fills nans by default (best)
    X, y, x_df = data_factory.create_xy(hist_df, testshift=0)
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)


@enforce_types
def _data_pp_ss_1exchange_1coin_1signal(csvdir: str) -> Tuple[DataPP, DataSS]:
    pp = DataPP(
        timeframe="5m",
        yval_exchange_id="kraken",
        yval_coin="ETH",
        usdcoin="USDT",
        yval_signal="high",
        N_test=2,
    )

    ss = DataSS(
        csv_dir=csvdir,
        st_timestamp=timestr_to_ut("2023-06-18"),
        fin_timestamp=timestr_to_ut("2023-06-21"),
        max_N_train=7,
        Nt=3,
        signals=[pp.yval_signal],
        coins=[pp.yval_coin],
        exchange_ids=[pp.yval_exchange_id],
    )
    return pp, ss


@enforce_types
def _assert_shapes(ss: DataSS, X: np.ndarray, y: np.ndarray, x_df: pd.DataFrame):
    assert X.shape[0] == y.shape[0]
    assert X.shape[0] == (ss.max_N_train + 1)  # 1 for test, rest for train
    assert X.shape[1] == ss.n

    assert len(x_df) == X.shape[0]
    assert len(x_df.columns) == ss.n


@enforce_types
def _df_from_raw_data(raw_data: list) -> pd.DataFrame:
    df = initialize_df(TOHLCV_COLS)
    next_df = pd.DataFrame(raw_data, columns=TOHLCV_COLS)
    df = concat_next_df(df, next_df)
    return df
