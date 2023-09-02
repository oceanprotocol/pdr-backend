from enforce_typing import enforce_types

from pdr_backend.models.feed import dictToFeed, Feed


@enforce_types
def test_feed__construct_directly():
    feed = Feed(
        "Contract Name",
        "0x12345",
        "SYM:TEST",
        300,
        60,
        "0xowner",
        "BTC-USDT",
        "1h",
        "binance",
    )

    assert feed.name == "Contract Name"
    assert feed.address == "0x12345"
    assert feed.symbol == "SYM:TEST"
    assert feed.seconds_per_epoch == 300
    assert feed.seconds_per_subscription == 60
    assert feed.owner == "0xowner"
    assert feed.pair == "BTC-USDT"
    assert feed.timeframe == "1h"
    assert feed.source == "binance"
    assert feed.quote == "USDT"
    assert feed.base == "BTC"


@enforce_types
def test_feed__construct_via_dictToFeed():
    feed_dict = {
        "name": "Contract Name",
        "address": "0x12345",
        "symbol": "SYM:TEST",
        "seconds_per_epoch": 300,
        "seconds_per_subscription": 60,
        "owner": "0xowner",
        "pair": "BTC-USDT",
        "timeframe": "1h",
        "source": "binance",
    }
    feed = dictToFeed(feed_dict)
    assert isinstance(feed, Feed)

    assert feed.name == "Contract Name"
    assert feed.address == "0x12345"
    assert feed.symbol == "SYM:TEST"
    assert feed.seconds_per_epoch == 300
    assert feed.seconds_per_subscription == 60
    assert feed.owner == "0xowner"
    assert feed.pair == "BTC-USDT"
    assert feed.timeframe == "1h"
    assert feed.source == "binance"
    assert feed.base == "BTC"
    assert feed.quote == "USDT"

    # test pair with "/" (versus "-")
    feed_dict["pair"] = "BTC/USDT"
    feed = dictToFeed(feed_dict)
    assert feed.base == "BTC"
    assert feed.quote == "USDT"
