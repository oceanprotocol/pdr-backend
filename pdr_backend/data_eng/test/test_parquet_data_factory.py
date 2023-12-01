import os
import time
from typing import List

from enforce_typing import enforce_types
import numpy as np
import polars as pl
import pytest

from pdr_backend.data_eng.constants import TOHLCV_SCHEMA_PL
from pdr_backend.data_eng.parquet_data_factory import ParquetDataFactory
from pdr_backend.data_eng.plutil import (
    initialize_df,
    transform_df,
    load_parquet,
    save_parquet,
    concat_next_df,
)
from pdr_backend.data_eng.test.resources import (
    _data_pp_ss_1feed,
    _data_pp,
    _data_ss,
    ETHUSDT_PARQUET_DFS,
)
from pdr_backend.util.constants import S_PER_MIN
from pdr_backend.util.mathutil import all_nan, has_nan
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
    """
    @arguments
      n_uts -- expected # timestamps. Typically int. If '>1K', expect >1000
    """

    # setup: uts helpers
    def _calc_ut(since: int, i: int) -> int:
        """Return a ut : unix time, in ms, in UTC time zone"""
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

    _, ss, pq_data_factory, _ = _data_pp_ss_1feed(
        tmpdir,
        "binanceus h ETH/USDT",
        st_timestr,
        fin_timestr,
    )
    ss.exchs_dict["binanceus"] = FakeExchange()

    # setup: filename
    #   it's ok for input pair_str to have '/' or '-', it handles it
    #   but the output filename should not have '/' its pairstr part
    filename = pq_data_factory._hist_parquet_filename("binanceus", "ETH/USDT")
    filename2 = pq_data_factory._hist_parquet_filename("binanceus", "ETH-USDT")
    assert filename == filename2
    assert "ETH-USDT" in filename and "ETH/USDT" not in filename

    # ensure we check for unwanted "-". (Everywhere but filename, it's '/')
    with pytest.raises(AssertionError):
        pq_data_factory._update_hist_parquet_at_exch_and_pair(
            "binanceus", "ETH-USDT", ss.fin_timestamp
        )

    # work 1: new parquet
    pq_data_factory._update_hist_parquet_at_exch_and_pair(
        "binanceus", "ETH/USDT", ss.fin_timestamp
    )

    def _uts_in_parquet(filename: str) -> List[int]:
        df = load_parquet(filename)
        return df["timestamp"].to_list()

    uts: List[int] = _uts_in_parquet(filename)
    if isinstance(n_uts, int):
        assert len(uts) == n_uts
    elif n_uts == ">1K":
        assert len(uts) > 1000
    assert sorted(uts) == uts
    assert uts[0] == ss.st_timestamp
    assert uts[-1] == ss.fin_timestamp
    assert uts == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)

    # work 2: two more epochs at end --> it'll append existing parquet
    ss.d["fin_timestr"] = ut_to_timestr(ss.fin_timestamp + 2 * MS_PER_5M_EPOCH)
    pq_data_factory._update_hist_parquet_at_exch_and_pair(
        "binanceus", "ETH/USDT", ss.fin_timestamp
    )
    uts2 = _uts_in_parquet(filename)
    assert uts2 == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)

    # work 3: two more epochs at beginning *and* end --> it'll create new parquet
    ss.d["st_timestr"] = ut_to_timestr(ss.st_timestamp - 2 * MS_PER_5M_EPOCH)
    ss.d["fin_timestr"] = ut_to_timestr(ss.fin_timestamp + 4 * MS_PER_5M_EPOCH)
    pq_data_factory._update_hist_parquet_at_exch_and_pair(
        "binanceus", "ETH/USDT", ss.fin_timestamp
    )
    uts3 = _uts_in_parquet(filename)
    assert uts3 == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)


# ====================================================================
# test behavior of get_hist_df()


@enforce_types
def test_get_hist_df_happypath(tmpdir):
    """Is get_hist_df() executing e2e correctly? Incl. call to exchange.

    It may fail if the exchange is temporarily misbehaving, which
      shows up as a FileNotFoundError.
    So give it a few tries if needed.
    """
    n_tries = 5
    for try_i in range(n_tries - 1):
        try:
            _test_get_hist_df_happypath(tmpdir)
            return  # success

        except FileNotFoundError:
            print(f"test_get_hist_df_happypath try #{try_i+1}, file not found")
            time.sleep(2)

    # last chance
    _test_get_hist_df_happypath(tmpdir)


@enforce_types
def _test_get_hist_df_happypath(tmpdir):
    parquet_dir = str(tmpdir)

    pp = _data_pp(["binanceus h BTC/USDT"])
    ss = _data_ss(
        parquet_dir,
        ["binanceus h BTC-USDT,ETH/USDT", "kraken h BTC/USDT"],
        st_timestr="2023-06-18",
        fin_timestr="2023-06-19",
    )
    pq_data_factory = ParquetDataFactory(pp, ss)

    # call and assert
    hist_df = pq_data_factory.get_hist_df()

    # 289 records created
    assert len(hist_df) == 289

    # binanceus is returning valid data
    assert not has_nan(hist_df["binanceus:BTC/USDT:high"])
    assert not has_nan(hist_df["binanceus:ETH/USDT:high"])

    # kraken is returning nans
    assert has_nan(hist_df["kraken:BTC/USDT:high"])

    # assert head is oldest
    head_timestamp = hist_df.head(1)["timestamp"].to_list()[0]
    tail_timestamp = hist_df.tail(1)["timestamp"].to_list()[0]
    assert head_timestamp < tail_timestamp


@enforce_types
def test_hist_df__low_vs_high_level__1_no_nan(tmpdir):
    _test_hist_df__low_vs_high_level(tmpdir, ohlcv_val=12.1)


@enforce_types
def test_hist_df__low_vs_high_level__2_all_nan(tmpdir):
    _test_hist_df__low_vs_high_level(tmpdir, ohlcv_val=np.nan)


@enforce_types
def _test_hist_df__low_vs_high_level(tmpdir, ohlcv_val):
    """Does high-level behavior of hist_df() align with low-level implement'n?
    Should work whether no nans, or all nans (as set by ohlcv_val)
    """

    # setup
    _, _, pq_data_factory, _ = _data_pp_ss_1feed(tmpdir, "binanceus h BTC/USDT")
    filename = pq_data_factory._hist_parquet_filename("binanceus", "BTC/USDT")
    st_ut = pq_data_factory.ss.st_timestamp
    fin_ut = pq_data_factory.ss.fin_timestamp

    # mock
    n_pts = 20

    def mock_update_hist_pq(*args, **kwargs):  # pylint: disable=unused-argument
        s_per_epoch = S_PER_MIN * 5
        raw_tohlcv_data = [
            [st_ut + s_per_epoch * i] + [ohlcv_val] * 5 for i in range(n_pts)
        ]
        df = initialize_df()
        next_df = pl.DataFrame(raw_tohlcv_data, schema=TOHLCV_SCHEMA_PL)
        df = concat_next_df(df, next_df)
        df = transform_df(df)  # add "datetime" col, more
        save_parquet(filename, df)

    pq_data_factory._update_hist_parquet_at_exch_and_pair = mock_update_hist_pq

    # test 1: get hist_df via several low-level instrs, as get_hist_df() does
    pq_data_factory._update_parquet(fin_ut)
    assert os.path.getsize(filename) > 500

    df0 = pl.read_parquet(filename, columns=["high"])
    df1 = load_parquet(filename, ["high"], st_ut, fin_ut)
    parquet_dfs = (  # pylint: disable=assignment-from-no-return
        pq_data_factory._load_parquet(fin_ut)
    )
    hist_df = pq_data_factory._merge_parquet_dfs(parquet_dfs)

    assert len(df0) == len(df1) == len(df1["high"]) == len(hist_df) == n_pts
    if np.isnan(ohlcv_val):
        assert all_nan(df0)
        assert all_nan(df1["high"])
        assert all_nan(hist_df["binanceus:BTC/USDT:high"])
    else:
        assert not has_nan(df0)
        assert not has_nan(df1["high"])
        assert not has_nan(hist_df["binanceus:BTC/USDT:high"])

    # cleanup for test 2
    os.remove(filename)

    # test 2: get hist_df via a single high-level instr
    hist_df = pq_data_factory.get_hist_df()
    assert os.path.getsize(filename) > 500
    assert len(hist_df) == n_pts
    if np.isnan(ohlcv_val):
        assert all_nan(hist_df["binanceus:BTC/USDT:high"])
    else:
        assert not has_nan(hist_df["binanceus:BTC/USDT:high"])


@enforce_types
def test_exchange_hist_overlap(tmpdir):
    """DataFactory get_hist_df() and concat is executing e2e correctly"""
    _, _, pq_data_factory, _ = _data_pp_ss_1feed(
        tmpdir,
        "binanceus h ETH/USDT",
        st_timestr="2023-06-18",
        fin_timestr="2023-06-19",
    )

    # call and assert
    hist_df = pq_data_factory.get_hist_df()

    # 289 records created
    assert len(hist_df) == 289

    # assert head is oldest
    head_timestamp = hist_df.head(1)["timestamp"].to_list()[0]
    tail_timestamp = hist_df.tail(1)["timestamp"].to_list()[0]
    assert head_timestamp < tail_timestamp

    # let's get more data from exchange with overlap
    _, _, pq_data_factory2, _ = _data_pp_ss_1feed(
        tmpdir,
        "binanceus h ETH/USDT",
        st_timestr="2023-06-18",  # same
        fin_timestr="2023-06-20",  # different
    )
    hist_df2 = pq_data_factory2.get_hist_df()

    # assert on expected values
    # another 288 records appended
    # head (index = 0) still points to oldest date with tail (index = n) being the latest date
    assert len(hist_df2) == 289 + 288 == 577
    assert (
        hist_df2.head(1)["timestamp"].to_list()[0]
        < hist_df2.tail(1)["timestamp"].to_list()[0]
    )


@enforce_types
def test_hist_df_shape(tmpdir):
    _, _, pq_data_factory, _ = _data_pp_ss_1feed(tmpdir, "binanceus h ETH/USDT")
    hist_df = pq_data_factory._merge_parquet_dfs(ETHUSDT_PARQUET_DFS)
    assert isinstance(hist_df, pl.DataFrame)
    assert hist_df.columns == [
        "timestamp",
        "binanceus:ETH/USDT:open",
        "binanceus:ETH/USDT:high",
        "binanceus:ETH/USDT:low",
        "binanceus:ETH/USDT:close",
        "binanceus:ETH/USDT:volume",
        "datetime",
    ]
    assert hist_df.shape == (12, 7)
    assert len(hist_df["timestamp"]) == 12
    assert (  # pylint: disable=unsubscriptable-object
        hist_df["timestamp"][0] == 1686805500000
    )


# ====================================================================
# test if appropriate calls are made


@enforce_types
def test_get_hist_df_calls(tmpdir):
    """Test core DataFactory functions are being called"""
    _, _, pq_data_factory, _ = _data_pp_ss_1feed(tmpdir, "binanceus h ETH/USDT")

    # setup mock objects
    def mock_update_parquet(*args, **kwargs):  # pylint: disable=unused-argument
        mock_update_parquet.called = True

    def mock_load_parquet(*args, **kwargs):  # pylint: disable=unused-argument
        mock_load_parquet.called = True

    def mock_merge_parquet_dfs(*args, **kwargs):  # pylint: disable=unused-argument
        mock_merge_parquet_dfs.called = True
        return pl.DataFrame([1, 2, 3])

    pq_data_factory._update_parquet = mock_update_parquet
    pq_data_factory._load_parquet = mock_load_parquet
    pq_data_factory._merge_parquet_dfs = mock_merge_parquet_dfs

    # call and assert
    hist_df = pq_data_factory.get_hist_df()
    assert isinstance(hist_df, pl.DataFrame)
    assert len(hist_df) == 3

    assert mock_update_parquet.called
    assert mock_load_parquet.called
    assert mock_merge_parquet_dfs.called


@enforce_types
def test_get_hist_df_fns(tmpdir):
    """Test DataFactory get_hist_df functions are being called"""
    _, _, pq_data_factory, _ = _data_pp_ss_1feed(tmpdir, "binanceus h ETH/USDT")

    # setup mock objects
    def mock_update_parquet(*args, **kwargs):  # pylint: disable=unused-argument
        mock_update_parquet.called = True

    def mock_load_parquet(*args, **kwargs):  # pylint: disable=unused-argument
        mock_load_parquet.called = True

    def mock_merge_parquet_dfs(*args, **kwargs):  # pylint: disable=unused-argument
        mock_merge_parquet_dfs.called = True
        return pl.DataFrame([1, 2, 3])

    pq_data_factory._update_parquet = mock_update_parquet
    pq_data_factory._load_parquet = mock_load_parquet
    pq_data_factory._merge_parquet_dfs = mock_merge_parquet_dfs

    # call and assert
    hist_df = pq_data_factory.get_hist_df()
    assert len(hist_df) == 3

    assert mock_update_parquet.called
    assert mock_load_parquet.called
    assert mock_merge_parquet_dfs.called
