from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed, mock_feed, print_feeds


@enforce_types
def test_feed():
    feed = Feed(
        "Contract Name",
        "0x12345",
        "SYM:TEST",
        60,
        15,
        "0xowner",
        "BTC/USDT",
        "5m",
        "binance",
    )

    assert feed.name == "Contract Name"
    assert feed.address == "0x12345"
    assert feed.symbol == "SYM:TEST"
    assert feed.seconds_per_subscription == 60
    assert feed.trueval_submit_timeout == 15
    assert feed.owner == "0xowner"
    assert feed.pair == "BTC/USDT"
    assert feed.timeframe == "5m"
    assert feed.source == "binance"

    assert feed.seconds_per_epoch == 5 * 60
    assert feed.quote == "USDT"
    assert feed.base == "BTC"


@enforce_types
def test_mock_feed():
    feed = mock_feed("5m", "binance", "BTC/USDT")
    assert feed.timeframe == "5m"
    assert feed.source == "binance"
    assert feed.pair == "BTC/USDT"
    assert feed.address[:2] == "0x"
    assert len(feed.address) == 42  # ethereum sized address


@enforce_types
def test_feed__seconds_per_epoch():
    # 5m
    feed = mock_feed("5m", "binance", "BTC/USDT")
    assert feed.timeframe == "5m"
    assert feed.seconds_per_epoch == 5 * 60

    # 1h
    feed = mock_feed("1h", "binance", "BTC/USDT")
    assert feed.timeframe == "1h"
    assert feed.seconds_per_epoch == 60 * 60


@enforce_types
def test_feed__convert_pair():
    # start with '/', no convert needed
    feed = mock_feed("5m", "binance", "BTC/USDT")
    assert feed.pair == "BTC/USDT"

    # start with '-', convert to '/'
    feed = mock_feed("5m", "binance", "BTC-USDT")
    assert feed.pair == "BTC/USDT"


@enforce_types
def test_print_feeds():
    f1 = mock_feed("5m", "binance", "BTC/USDT")
    f2 = mock_feed("1h", "kraken", "BTC/USDT")
    feeds = {f1.address: f1, f2.address: f2}

    print_feeds(feeds)
    print_feeds(feeds, label=None)
    print_feeds(feeds, "my feeds")
