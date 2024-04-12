import os
import time
from typing import List
from unittest.mock import Mock, patch

from enforce_typing import enforce_types
import numpy as np
import polars as pl
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.lake.constants import TOHLCV_SCHEMA_PL
from pdr_backend.lake.merge_df import merge_rawohlcv_dfs
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.lake.plutil import (
    concat_next_df,
    initialize_rawohlcv_df,
    load_rawohlcv_file,
    save_rawohlcv_file,
)
from pdr_backend.lake.test.resources import _lake_ss_1feed, _lake_ss
from pdr_backend.util.constants import S_PER_MIN
from pdr_backend.util.mathutil import all_nan, has_nan
from pdr_backend.util.time_types import UnixTimeMs


MS_PER_5M_EPOCH = 300000


# ====================================================================
# test update of rawohlcv files


@enforce_types
@pytest.mark.parametrize(
    "st_timestr, fin_timestr, n_uts",
    [
        ("2023-01-01_0:00", "2023-01-01_0:00", 1),
        ("2023-01-01_0:00", "2023-01-01_0:05", 2),
        ("2023-01-01_0:00", "2023-01-01_0:10", 3),
        ("2023-01-01_0:00", "2023-01-01_0:45", 10),
        ("2023-01-01", "2023-06-21", ">1K"),
    ],
)
def test_update_rawohlcv_files(st_timestr: str, fin_timestr: str, n_uts, tmpdir):
    """
    @arguments
      n_uts -- expected # timestamps. Typically int. If '>1K', expect >1000
    """

    # setup: uts helpers
    def _calc_ut(since: int, i: int) -> int:
        """Return a ut : unix time, in ms, in UTC time zone"""
        return UnixTimeMs(since + i * MS_PER_5M_EPOCH)

    def _uts_in_range(st_ut: int, fin_ut: int, limit_N=100000) -> List[int]:
        return [
            _calc_ut(st_ut, i) for i in range(limit_N) if _calc_ut(st_ut, i) <= fin_ut
        ]

    # setup: exchange
    class FakeExchange:
        def __init__(self):
            self.cur_ut: int = int(UnixTimeMs.now())  # fixed value, for easier testing

        # pylint: disable=unused-argument
        def fetch_ohlcv(self, since, limit, *args, **kwargs) -> list:
            uts: List[int] = _uts_in_range(since, self.cur_ut, limit)
            return [[ut] + [1.0] * 5 for ut in uts]  # 1.0 for open, high, ..

    ss, factory = _lake_ss_1feed(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # setup: filename
    #   it's ok for input pair_str to have '/' or '-', it handles it
    #   but the output filename should not have '/' its pairstr part
    feed = ArgFeed("binanceus", None, "ETH/USDT", "5m")
    filename = factory._rawohlcv_filename(feed)
    feed = ArgFeed("binanceus", None, "ETH/USDT", "5m")
    filename2 = factory._rawohlcv_filename(feed)
    assert filename == filename2
    assert "ETH-USDT" in filename and "ETH/USDT" not in filename

    # work 1: new rawohlcv file
    feed = ArgFeed("binanceus", None, "ETH/USDT", "5m")

    with patch("ccxt.binanceus") as mock:
        mock.return_value = FakeExchange()
        factory._update_rawohlcv_files_at_feed(feed, ss.fin_timestamp)

    def _uts_in_rawohlcv_file(filename: str) -> List[int]:
        df = load_rawohlcv_file(filename)
        return df["timestamp"].to_list()

    uts: List[int] = _uts_in_rawohlcv_file(filename)
    if isinstance(n_uts, int):
        assert len(uts) == n_uts
    elif n_uts == ">1K":
        assert len(uts) > 1000
    assert sorted(uts) == uts
    assert uts[0] == ss.st_timestamp
    assert uts[-1] == ss.fin_timestamp
    assert uts == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)

    # work 2: two more epochs at end --> it'll append existing file
    ss.d["fin_timestr"] = UnixTimeMs(
        ss.fin_timestamp + 2 * MS_PER_5M_EPOCH
    ).to_timestr()

    with patch("ccxt.binanceus") as mock:
        mock.return_value = FakeExchange()
        factory._update_rawohlcv_files_at_feed(feed, ss.fin_timestamp)
    uts2 = _uts_in_rawohlcv_file(filename)
    assert uts2 == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)

    # work 3: two more epochs at beginning *and* end --> it'll create new file
    ss.d["st_timestr"] = UnixTimeMs(ss.st_timestamp - 2 * MS_PER_5M_EPOCH).to_timestr()
    ss.d["fin_timestr"] = UnixTimeMs(
        ss.fin_timestamp + 4 * MS_PER_5M_EPOCH
    ).to_timestr()

    with patch("ccxt.binanceus") as mock:
        mock.return_value = FakeExchange()
        factory._update_rawohlcv_files_at_feed(feed, ss.fin_timestamp)
    uts3 = _uts_in_rawohlcv_file(filename)
    assert uts3 == _uts_in_range(ss.st_timestamp, ss.fin_timestamp)


# ====================================================================
# test behavior of get_mergedohlcv_df()


@enforce_types
def test_get_mergedohlcv_df_happypath(tmpdir):
    """Is get_mergedohlcv_df() executing e2e correctly?
    Includes actual calls to the exchange API, eg binance or kraken, via ccxt.

    It may fail if the exchange is temporarily misbehaving, which
      shows up as a FileNotFoundError.
    So give it a few tries if needed.
    """
    n_tries = 5
    for try_i in range(n_tries - 1):
        try:
            _test_get_mergedohlcv_df_happypath_onetry(tmpdir)
            return  # success

        except FileNotFoundError:
            print(f"test_get_mergedohlcv_df_happypath try #{try_i+1}, file not found")
            time.sleep(2)

    # last chance
    _test_get_mergedohlcv_df_happypath_onetry(tmpdir)


@enforce_types
def _test_get_mergedohlcv_df_happypath_onetry(tmpdir):
    lake_dir = str(tmpdir)

    ss = _lake_ss(
        lake_dir,
        ["binanceus BTC-USDT,ETH/USDT h 5m", "kraken BTC/USDT h 5m"],
        st_timestr="2023-06-18",
        fin_timestr="2023-06-19",
    )
    factory = OhlcvDataFactory(ss)

    # call and assert
    mergedohlcv_df = factory.get_mergedohlcv_df()

    # 289 records created
    assert len(mergedohlcv_df) == 289

    # binanceus is returning valid data
    assert not has_nan(mergedohlcv_df["binanceus:BTC/USDT:high"])
    assert not has_nan(mergedohlcv_df["binanceus:ETH/USDT:high"])

    # kraken is returning nans
    assert has_nan(mergedohlcv_df["kraken:BTC/USDT:high"])

    # assert head is oldest
    head_timestamp = mergedohlcv_df.head(1)["timestamp"].to_list()[0]
    tail_timestamp = mergedohlcv_df.tail(1)["timestamp"].to_list()[0]
    assert head_timestamp < tail_timestamp


@enforce_types
def test_mergedohlcv_df__low_vs_high_level__1_no_nan(tmpdir):
    _test_mergedohlcv_df__low_vs_high_level(tmpdir, ohlcv_val=12.1)


@enforce_types
def test_mergedohlcv_df__low_vs_high_level__2_all_nan(tmpdir):
    _test_mergedohlcv_df__low_vs_high_level(tmpdir, ohlcv_val=np.nan)


@enforce_types
def _test_mergedohlcv_df__low_vs_high_level(tmpdir, ohlcv_val):
    """Does high-level behavior of mergedohlcv_df() align with low-level implement'n?
    Should work whether no nans, or all nans (as set by ohlcv_val)
    """

    # setup
    _, factory = _lake_ss_1feed(tmpdir, "binanceus BTC/USDT h 5m")
    filename = factory._rawohlcv_filename(
        ArgFeed("binanceus", "high", "BTC/USDT", "5m")
    )
    st_ut = factory.ss.st_timestamp
    fin_ut = factory.ss.fin_timestamp

    # mock
    n_pts = 20

    def mock_update(*args, **kwargs):  # pylint: disable=unused-argument
        s_per_epoch = S_PER_MIN * 5
        raw_tohlcv_data = [
            [st_ut + s_per_epoch * i] + [ohlcv_val] * 5 for i in range(n_pts)
        ]
        df = initialize_rawohlcv_df()
        next_df = pl.DataFrame(raw_tohlcv_data, schema=TOHLCV_SCHEMA_PL)
        df = concat_next_df(df, next_df)
        save_rawohlcv_file(filename, df)

    factory._update_rawohlcv_files_at_feed = mock_update

    # test 1: get mergedohlcv_df via several low-level instrs, as get_mergedohlcv_df() does
    factory._update_rawohlcv_files(fin_ut)
    assert os.path.getsize(filename) > 500

    df0 = pl.read_parquet(filename, columns=["high"])
    df1 = load_rawohlcv_file(filename, ["high"], st_ut, fin_ut)
    rawohlcv_dfs = (  # pylint: disable=assignment-from-no-return
        factory._load_rawohlcv_files(fin_ut)
    )
    mergedohlcv_df = merge_rawohlcv_dfs(rawohlcv_dfs)

    assert len(df0) == len(df1) == len(df1["high"]) == len(mergedohlcv_df) == n_pts
    if np.isnan(ohlcv_val):
        assert all_nan(df0)
        assert all_nan(df1["high"])
        assert all_nan(mergedohlcv_df["binanceus:BTC/USDT:high"])
    else:
        assert not has_nan(df0)
        assert not has_nan(df1["high"])
        assert not has_nan(mergedohlcv_df["binanceus:BTC/USDT:high"])

    # cleanup for test 2
    os.remove(filename)

    # test 2: get mergedohlcv_df via a single high-level instr
    mergedohlcv_df = factory.get_mergedohlcv_df()
    assert os.path.getsize(filename) > 500
    assert len(mergedohlcv_df) == n_pts
    if np.isnan(ohlcv_val):
        assert all_nan(mergedohlcv_df["binanceus:BTC/USDT:high"])
    else:
        assert not has_nan(mergedohlcv_df["binanceus:BTC/USDT:high"])


@enforce_types
def test_exchange_hist_overlap(tmpdir):
    """DataFactory get_mergedohlcv_df() and concat is executing e2e correctly"""
    _, factory = _lake_ss_1feed(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr="2023-06-18",
        fin_timestr="2023-06-19",
    )

    # call and assert
    mergedohlcv_df = factory.get_mergedohlcv_df()

    # 289 records created
    assert len(mergedohlcv_df) == 289

    # assert head is oldest
    head_timestamp = mergedohlcv_df.head(1)["timestamp"].to_list()[0]
    tail_timestamp = mergedohlcv_df.tail(1)["timestamp"].to_list()[0]
    assert head_timestamp < tail_timestamp

    # let's get more data from exchange with overlap
    _, factory2 = _lake_ss_1feed(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr="2023-06-18",  # same
        fin_timestr="2023-06-20",  # different
    )
    mergedohlcv_df2 = factory2.get_mergedohlcv_df()

    # assert on expected values
    # another 288 records appended
    # head (index = 0) still points to oldest date with tail (index = n) being the latest date
    assert len(mergedohlcv_df2) == 289 + 288 == 577
    assert (
        mergedohlcv_df2.head(1)["timestamp"].to_list()[0]
        < mergedohlcv_df2.tail(1)["timestamp"].to_list()[0]
    )


@enforce_types
@patch("pdr_backend.lake.ohlcv_data_factory.merge_rawohlcv_dfs")
def test_get_mergedohlcv_df_calls(
    mock_merge_rawohlcv_dfs,
    tmpdir,
):
    mock_merge_rawohlcv_dfs.return_value = Mock(spec=pl.DataFrame)
    _, factory = _lake_ss_1feed(tmpdir, "binanceus ETH/USDT h 5m")

    factory._update_rawohlcv_files = Mock(return_value=None)
    factory._load_rawohlcv_files = Mock(return_value=None)

    mergedohlcv_df = factory.get_mergedohlcv_df()

    assert isinstance(mergedohlcv_df, pl.DataFrame)

    factory._update_rawohlcv_files.assert_called()
    factory._load_rawohlcv_files.assert_called()
    mock_merge_rawohlcv_dfs.assert_called()


# =======================================================================
# issue #657

tohlcv_data1 = [
    [1709887500000, 3943.99, 3952.91, 3942.95, 3943.73, 2554.4607],
    [1709887800000, 3943.72, 3950.52, 3943.66, 3943.88, 1373.67],
    [1709888100000, 3943.87, 3950.45, 3939.4, 3940.03, 1514.3544],
    [1709888400000, 3940.03, 3945.4, 3930.0, 3934.19, 1659.3454],
    [1709888700000, 3934.19, 3936.2, 3930.2, 3933.0, 1607.2883],
    [1709889000000, 3933.0, 3950.73, 3930.57, 3948.14, 3421.5831],
    [1709889300000, 3948.15, 3949.29, 3942.35, 3943.61, 2034.7834],
    [1709889600000, 3943.61, 3946.19, 3935.16, 3937.58, 1659.4638],
    [1709889900000, 3937.58, 3941.11, 3934.6, 3938.53, 801.3086],
    [1709890200000, 3938.53, 3948.19, 3935.94, 3941.24, 2356.8294],
    [1709890500000, 3941.25, 3950.49, 3941.24, 3946.01, 2243.4569],
    [1709890800000, 3946.0, 3949.72, 3943.14, 3944.22, 1262.2829],
    [1709891100000, 3944.22, 3946.25, 3944.22, 3946.25, 116.9614],
]

tohlcv_data2 = [
    [1709887500000, 67289.04, 67390.0, 67274.7, 67300.0, 118.03242],
    [1709887800000, 67300.01, 67320.0, 67256.4, 67256.41, 68.07976],
    [1709888100000, 67256.4, 67291.97, 67200.01, 67208.55, 114.46873],
    [1709888400000, 67208.56, 67213.19, 67040.76, 67070.82, 173.93243],
    [1709888700000, 67070.82, 67120.57, 67050.0, 67100.0, 175.64183],
    [1709889000000, 67100.0, 67223.54, 67095.16, 67216.42, 155.12712],
]


@enforce_types
def test_issue657_infer_orientation():
    # the following line will *not* cause an issue
    # -this mimics how the code looked before the fix
    # -it infers orient="row"
    pl.DataFrame(tohlcv_data1, schema=TOHLCV_SCHEMA_PL)

    # the following line *will* cause an issue
    # -this mimics how the code looked before the fix
    # -it infers orient="col", and therein lies the issue!
    # -because it's casting [1709887500000, 67289.04, 67390.0, ..] as timestamps
    with pytest.raises(TypeError):
        pl.DataFrame(tohlcv_data2, schema=TOHLCV_SCHEMA_PL)


@enforce_types
def test_issue657_set_col_orientation():
    # the following line *will* cause an issue
    # - it's = the code before the fix, plus orient="col" (vs inferring)
    with pytest.raises(TypeError):
        pl.DataFrame(tohlcv_data1, schema=TOHLCV_SCHEMA_PL, orient="col")

    # the following line *will* cause an issue
    # - it's = the code before the fix, plus orient="col" (vs inferring)
    with pytest.raises(TypeError):
        pl.DataFrame(tohlcv_data2, schema=TOHLCV_SCHEMA_PL, orient="col")


@enforce_types
def test_issue657_set_row_orientation():
    # the following line will *not* cause an issue
    # - it's = the code before the fix, plus orient="row" (vs inferring)
    pl.DataFrame(tohlcv_data1, schema=TOHLCV_SCHEMA_PL, orient="row")

    # the following line will *not* cause an issue
    # - it's = the code before the fix, plus orient="row" (vs inferring)
    pl.DataFrame(tohlcv_data2, schema=TOHLCV_SCHEMA_PL, orient="row")
