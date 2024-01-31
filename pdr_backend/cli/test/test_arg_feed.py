import ccxt
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.util.mocks import MockExchange


@enforce_types
def test_ArgFeed_main_constructor():
    # ok
    tups = [
        ("binance", "open", "BTC/USDT"),
        ("kraken", "close", "BTC/DAI"),
        ("kraken", "close", "BTC-DAI"),
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
    ]
    for feed_tup in tups:
        with pytest.raises(ValueError):
            ArgFeed(*feed_tup)

    # not ok - Type Error
    tups = [
        (),
        ("binance", "open", "BTC/USDT", "", ""),
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


def test_ccxt_exchange():
    feed = ArgFeed("binance", "open", "BTC/USDT")
    assert isinstance(feed.ccxt_exchange(), ccxt.Exchange)
    assert isinstance(feed.ccxt_exchange(mock=False), ccxt.Exchange)
    assert isinstance(feed.ccxt_exchange(mock=True), MockExchange)
