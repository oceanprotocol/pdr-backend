from enforce_typing import enforce_types

from pdr_backend.models.feed import dictToFeed, Feed


@enforce_types
def test_feed1():
    feed = Feed(
        "Contract Name",
        "0x12345",
        "test",
        300,
        60,
        15,
        "0xowner",
        "BTC-ETH",
        "1h",
        "binance",
    )

    assert feed.name == "Contract Name"
    assert feed.address == "0x12345"
    assert feed.symbol == "test"
    assert feed.seconds_per_epoch == 300
    assert feed.seconds_per_subscription == 60
    assert feed.trueval_submit_timeout == 15
    assert feed.owner == "0xowner"
    assert feed.pair == "BTC-ETH"
    assert feed.timeframe == "1h"
    assert feed.source == "binance"
    assert feed.quote == "ETH"
    assert feed.base == "BTC"


@enforce_types
def test_feed2():
    feed_dict = {
        "name": "Contract Name",
        "address": "0x12345",
        "symbol": "test",
        "seconds_per_epoch": 300,
        "seconds_per_subscription": 60,
        "trueval_submit_timeout": 15,
        "owner": "0xowner",
        "pair": "BTC-ETH",
        "timeframe": "1h",
        "source": "binance",
    }
    feed = dictToFeed(feed_dict)
    assert isinstance(feed, Feed)

    assert feed.name == "Contract Name"
    assert feed.address == "0x12345"
    assert feed.symbol == "test"
    assert feed.seconds_per_epoch == 300
    assert feed.seconds_per_subscription == 60
    assert feed.trueval_submit_timeout == 15
    assert feed.owner == "0xowner"
    assert feed.pair == "BTC-ETH"
    assert feed.timeframe == "1h"
    assert feed.source == "binance"
    assert feed.quote == "ETH"
    assert feed.base == "BTC"
