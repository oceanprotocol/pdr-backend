import copy
import os

import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.util.timeutil import timestr_to_ut

_D = {
    "feeds": ["kraken ETH/USDT 5m", "binanceus ETH/USDT,TRX/DAI 1h"],
    "parquet_dir": "parquet_data",
    "st_timestr": "2023-06-18",
    "fin_timestr": "2023-06-21",
}


@enforce_types
def test_lake_ss_basic():
    ss = LakeSS(_D)

    # yaml properties
    assert "parquet_data" in ss.parquet_dir
    assert ss.st_timestr == "2023-06-18"
    assert ss.fin_timestr == "2023-06-21"

    assert ss.exchange_strs == set(["binanceus", "kraken"])

    # derivative properties
    assert ss.st_timestamp == timestr_to_ut("2023-06-18")
    assert ss.fin_timestamp == timestr_to_ut("2023-06-21")
    assert ss.feeds == ArgFeeds(
        [
            ArgFeed("kraken", None, "ETH/USDT", "5m"),
            ArgFeed("binanceus", None, "ETH/USDT", "1h"),
            ArgFeed("binanceus", None, "TRX/DAI", "1h"),
        ]
    )
    assert ss.exchange_pair_tups == set(
        [
            ("kraken", "ETH/USDT"),
            ("binanceus", "ETH/USDT"),
            ("binanceus", "TRX/DAI"),
        ]
    )
    assert len(ss.feeds) == ss.n_feeds == 3
    assert ss.n_exchs == 2
    assert len(ss.exchange_strs) == 2
    assert "binanceus" in ss.exchange_strs

    # test str
    assert "LakeSS" in str(ss)

    assert isinstance(ss.copy(), LakeSS)


@enforce_types
def test_lake_ss_now():
    d = copy.deepcopy(_D)
    d["fin_timestr"] = "now"
    ss = LakeSS(d)

    assert ss.fin_timestr == "now"

    ut2 = timestr_to_ut("now")
    assert ss.fin_timestamp / 1000 == pytest.approx(ut2 / 1000, 1.0)


@enforce_types
def test_parquet_dir(tmpdir):
    # rel path given; needs an abs path
    d = copy.deepcopy(_D)
    d["parquet_dir"] = "parquet_data"
    ss = LakeSS(d)
    target_parquet_dir = os.path.abspath("parquet_data")
    assert ss.parquet_dir == target_parquet_dir

    # abs path given
    d = copy.deepcopy(_D)
    d["parquet_dir"] = os.path.join(tmpdir, "parquet_data")
    ss = LakeSS(d)
    target_parquet_dir = os.path.join(tmpdir, "parquet_data")
    assert ss.parquet_dir == target_parquet_dir
