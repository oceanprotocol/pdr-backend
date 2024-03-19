import copy
import os

import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.util.time_types import UnixTimeMs

_D = {
    "feeds": ["kraken ETH/USDT 5m", "binanceus ETH/USDT,TRX/DAI 1h"],
    "lake_dir": "lake_data",
    "st_timestr": "2023-06-18",
    "fin_timestr": "2023-06-21",
}


@enforce_types
def test_lake_ss_basic():
    ss = LakeSS(_D)

    # yaml properties
    assert "lake_data" in ss.lake_dir
    assert ss.st_timestr == "2023-06-18"
    assert ss.fin_timestr == "2023-06-21"

    assert ss.exchange_strs == set(["binanceus", "kraken"])

    # derivative properties
    assert ss.st_timestamp == UnixTimeMs.from_timestr("2023-06-18")
    assert ss.fin_timestamp == UnixTimeMs.from_timestr("2023-06-21")
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


@enforce_types
def test_lake_ss_now():
    d = copy.deepcopy(_D)
    d["fin_timestr"] = "now"
    ss = LakeSS(d)

    assert ss.fin_timestr == "now"

    ut2 = UnixTimeMs.from_timestr("now")
    assert ss.fin_timestamp / 1000 == pytest.approx(ut2 / 1000, 1.0)


@enforce_types
def test_lake_dir(tmpdir):
    # rel path given; needs an abs path
    d = copy.deepcopy(_D)
    d["lake_dir"] = "lake_data"
    ss = LakeSS(d)
    target_lake_dir = os.path.abspath("lake_data")
    assert ss.lake_dir == target_lake_dir

    # abs path given
    d = copy.deepcopy(_D)
    d["lake_dir"] = os.path.join(tmpdir, "lake_data")
    ss = LakeSS(d)
    target_lake_dir = os.path.join(tmpdir, "lake_data")
    assert ss.lake_dir == target_lake_dir
