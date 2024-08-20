#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed


@enforce_types
def test_ArgFeed_main_constructor():
    # ok
    tups = [
        ("binance", "open", "BTC/USDT"),
        ("kraken", "close", "BTC/DAI"),
        ("kraken", "close", "BTC-DAI"),
        ("binance", "open", "BTC/USDT", "5m", "vb_201"),
        ("binance", "open", "BTC/USDT", "5m", "tb_201"),
        ("binance", "open", "BTC/USDT", "5m", "db_201.5"),
    ]
    for feed_tup in tups:
        ArgFeed(*feed_tup)

    # not ok - Value Error
    tups = [
        ("binance", "open", ""),
        ("xyz", "open", "BTC/USDT"),
        ("xyz", "open", "BTC-USDT"),
        ("binance", "xyz", "BTC/USDT"),
        ("binance", "open", "BTC/XYZ"),
        ("binance", "open"),
        ("binance", "open", "BTC/USDT", "5m", "201"),
        ("binance", "open", "BTC/USDT", "5m", "tb-201.5"),
    ]
    for feed_tup in tups:
        with pytest.raises(ValueError):
            ArgFeed(*feed_tup)

    # not ok - Type Error
    tups = [
        (),
    ]
    for feed_tup in tups:
        with pytest.raises(TypeError):
            ArgFeed(*feed_tup)


@enforce_types
def test_ArgFeed_from_str():
    target_feed = ArgFeed("binance", "close", "BTC/USDT")
    assert ArgFeed.from_str("binance BTC/USDT c") == target_feed
    assert ArgFeed.from_str("binance BTC-USDT c") == target_feed

    target_feed = ArgFeed("binance", "close", "BTC/USDT", "1h")
    assert ArgFeed.from_str("binance BTC/USDT c 1h") == target_feed
    assert ArgFeed.from_str("binance BTC-USDT c 1h") == target_feed

    target_feed = ArgFeed("binance", "close", "BTC/USDT", "1s", "vb_201")
    assert ArgFeed.from_str("binance BTC/USDT c 1s vb_201") == target_feed

    target_feed = ArgFeed("binance", "close", "BTC/USDT", "1s", "tb_201")
    assert ArgFeed.from_str("binance BTC/USDT c 1s tb_201") == target_feed

    target_feed = ArgFeed("binance", "close", "BTC/USDT", "1s", "db_201.5")
    assert ArgFeed.from_str("binance BTC/USDT c 1s db_201.5") == target_feed


@enforce_types
def test_ArgFeed_str():
    target_feed_str = "binance BTC/USDT o"
    assert str(ArgFeed("binance", "open", "BTC/USDT")) == target_feed_str
    assert str(ArgFeed("binance", "open", "BTC-USDT")) == target_feed_str

    target_feed_str = "binance BTC/USDT o 5m"
    assert str(ArgFeed("binance", "open", "BTC/USDT", "5m")) == target_feed_str
    assert str(ArgFeed("binance", "open", "BTC-USDT", "5m")) == target_feed_str

    target_feed_str = "binance BTC/USDT 5m"
    assert str(ArgFeed("binance", None, "BTC/USDT", "5m")) == target_feed_str
    assert str(ArgFeed("binance", None, "BTC-USDT", "5m")) == target_feed_str

    target_feed_str = "binance BTC/USDT 5m vb_201"
    assert str(ArgFeed("binance", None, "BTC/USDT", "5m", "vb_201")) == target_feed_str
    assert str(ArgFeed("binance", None, "BTC-USDT", "5m", "vb_201")) == target_feed_str

    target_feed_str = "binance BTC/USDT 5m db_201"
    assert (
        str(ArgFeed("binance", None, "BTC/USDT", "5m", "db_201"))
        == target_feed_str
    )
    assert (
        str(ArgFeed("binance", None, "BTC-USDT", "5m", "db_201"))
        == target_feed_str
    )