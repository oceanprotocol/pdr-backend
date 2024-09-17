#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import os
from datetime import timedelta

import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.lake_ss import LakeSS, lake_ss_test_dict
from pdr_backend.util.time_types import UnixTimeMs, dt_now_UTC

_D = {
    "feeds": ["kraken ETH/USDT 5m", "binanceus ETH/USDT,TRX/DAI 1h"],
    "lake_dir": "lake_data",
    "st_timestr": "2023-06-18",
    "fin_timestr": "2023-06-21",
    "export_db_data_to_parquet_files": True,
    "seconds_between_parquet_exports": 3600,
    "number_of_files_after_which_re_export_db": 100,
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


def test_lake_ss_start_time():
    d = copy.deepcopy(_D)
    d["st_timestr"] = "3 days ago"
    d["fin_timestr"] = "now"
    ss = LakeSS(d)

    assert ss.st_timestr == "3 days ago"

    ut2 = dt_now_UTC() - timedelta(days=3)
    assert ss.st_timestamp / 1000 == pytest.approx(ut2.timestamp(), 1.0)


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


@enforce_types
def test_lake_ss_test_dict_1_default_feeds(tmpdir):
    lake_dir = os.path.join(tmpdir, "lake_data")

    d = lake_ss_test_dict(lake_dir)

    assert d["lake_dir"] == lake_dir

    f = d["feeds"][0]
    assert "binance" in f or "kraken" in f
    assert "BTC" in f or "ETH" in f
    assert "5m" in f or "1h" in f

    assert "st_timestr" in d
    assert "fin_timestr" in d
    assert "timeframe" in d

    ss = LakeSS(d)
    assert ss.lake_dir == lake_dir
    assert ss.feeds


@enforce_types
def test_lake_ss_test_dict_2_specify_feeds(tmpdir):
    lake_dir = os.path.join(tmpdir, "lake_data")
    feeds = ["kraken DOT/USDT c 60m"]
    d = lake_ss_test_dict(lake_dir, feeds)
    assert d["lake_dir"] == lake_dir
    assert d["feeds"] == feeds


@enforce_types
def test_lake_ss_test_dict_3_nondefault_time_settings(tmpdir):
    lake_dir = os.path.join(tmpdir, "lake_data")
    d = lake_ss_test_dict(
        lake_dir,
        st_timestr="2023-01-20",
        fin_timestr="2023-01-21",
        timeframe="1h",
    )
    assert d["st_timestr"] == "2023-01-20"
    assert d["fin_timestr"] == "2023-01-21"
    assert d["timeframe"] == "1h"
