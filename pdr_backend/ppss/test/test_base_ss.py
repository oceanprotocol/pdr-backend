import ccxt
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.base_ss import MultiFeedMixin, SingleFeedMixin
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed


class MultiFeedMixinTest(MultiFeedMixin):
    FEEDS_KEY = "feeds"


class SingleFeedMixinTest(SingleFeedMixin):
    FEED_KEY = "feed"


@enforce_types
def test_multi_feed():
    d = {
        "feeds": ["kraken ETH/USDT hc", "binanceus ETH/USDT,TRX/DAI h"],
    }
    ss = MultiFeedMixinTest(d)
    MultiFeedMixinTest(d, assert_feed_attributes=[])
    MultiFeedMixinTest(d, assert_feed_attributes=["exchange", "pair", "signal"])

    with pytest.raises(AssertionError):
        MultiFeedMixinTest(d, assert_feed_attributes=["timeframe"])

    assert ss.feeds_strs == ["kraken ETH/USDT hc", "binanceus ETH/USDT,TRX/DAI h"]
    assert ss.n_exchs == 2
    assert ss.exchange_strs == {"kraken", "binanceus"}
    assert ss.n_feeds == 4
    assert ss.feeds == ArgFeeds(
        [
            ArgFeed("kraken", "high", "ETH/USDT"),
            ArgFeed("kraken", "close", "ETH/USDT"),
            ArgFeed("binanceus", "high", "ETH/USDT"),
            ArgFeed("binanceus", "high", "TRX/DAI"),
        ]
    )
    assert ss.exchange_pair_tups == {
        ("kraken", "ETH/USDT"),
        ("binanceus", "ETH/USDT"),
        ("binanceus", "TRX/DAI"),
    }


@enforce_types
def test_multi_feed_filter():
    d = {
        "feeds": ["kraken ETH/USDT 5m", "binanceus ETH/USDT,TRX/DAI 1h"],
    }
    ss = MultiFeedMixinTest(d)

    cand_feeds = {
        "0x12345": SubgraphFeed(
            "",
            "0x12345",
            "test",
            60,
            15,
            "0xowner",
            "BTC/ETH",
            "1h",
            "binance",
        )
    }

    assert ss.filter_feeds_from_candidates(cand_feeds) == {}

    cand_feeds = {
        "0x12345": SubgraphFeed(
            "",
            "0x12345",
            "test",
            60,
            15,
            "0xowner",
            "ETH/USDT",
            "5m",
            "kraken",
        )
    }

    assert ss.filter_feeds_from_candidates(cand_feeds) == cand_feeds

    cand_feeds = {
        "0x12345": SubgraphFeed(
            "",
            "0x12345",
            "test",
            60,
            15,
            "0xowner",
            "ETH/USDT",
            "5m",
            "kraken",
        ),
        "0x67890": SubgraphFeed(
            "",
            "0x67890",
            "test",
            60,
            15,
            "0xowner",
            "ETH/USDT",
            "1h",
            "binanceus",
        ),
    }

    assert ss.filter_feeds_from_candidates(cand_feeds) == cand_feeds

    cand_feeds = {
        "0x12345": SubgraphFeed(
            "",
            "0x12345",
            "test",
            60,
            15,
            "0xowner",
            "ETH/USDT",
            "5m",
            "kraken",
        ),
        "0x67890": SubgraphFeed(
            "",
            "0x67890",
            "test",
            60,
            15,
            "0xowner",
            "ETH/DAI",
            "1h",
            "binanceus",
        ),
    }

    assert ss.filter_feeds_from_candidates(cand_feeds) == {
        "0x12345": cand_feeds["0x12345"]
    }


@enforce_types
def test_single_feed():
    d = {"feed": "kraken ETH/USDT h"}
    ss = SingleFeedMixinTest(d)
    SingleFeedMixinTest(d, assert_feed_attributes=[])
    SingleFeedMixinTest(d, assert_feed_attributes=["exchange", "pair", "signal"])

    with pytest.raises(AssertionError):
        SingleFeedMixinTest(d, assert_feed_attributes=["timeframe"])

    d = {"feed": "kraken ETH/USDT 1h"}
    ss = SingleFeedMixinTest(d)
    assert ss.feed == ArgFeed("kraken", None, "ETH/USDT", "1h")
    assert ss.pair_str == "ETH/USDT"
    assert ss.exchange_str == "kraken"
    assert ss.exchange_class == ccxt.kraken
    assert ss.signal_str == ""
    assert ss.base_str == "ETH"
    assert ss.quote_str == "USDT"
    assert ss.timeframe == "1h"
    assert ss.timeframe_ms == 3600000
    assert ss.timeframe_s == 3600
    assert ss.timeframe_m == 60


@enforce_types
def test_single_feed_filter():
    d = {"feed": "kraken ETH/USDT 5m"}
    ss = SingleFeedMixinTest(d)

    cand_feeds = {
        "0x12345": SubgraphFeed(
            "",
            "0x12345",
            "test",
            60,
            15,
            "0xowner",
            "BTC/ETH",
            "1h",
            "binance",
        )
    }

    assert ss.get_feed_from_candidates(cand_feeds) is None

    cand_feeds = {
        "0x12345": SubgraphFeed(
            "",
            "0x12345",
            "test",
            60,
            15,
            "0xowner",
            "ETH/USDT",
            "5m",
            "kraken",
        )
    }

    assert ss.get_feed_from_candidates(cand_feeds) == cand_feeds["0x12345"]

    cand_feeds = {
        "0x12345": SubgraphFeed(
            "",
            "0x12345",
            "test",
            60,
            15,
            "0xowner",
            "ETH/USDT",
            "5m",
            "kraken",
        ),
        "0x67890": SubgraphFeed(
            "",
            "0x67890",
            "test",
            60,
            15,
            "0xowner",
            "ETH/USDT",
            "1h",
            "binanceus",
        ),
    }

    assert ss.get_feed_from_candidates(cand_feeds) == cand_feeds["0x12345"]

    cand_feeds = {
        "0x12345": SubgraphFeed(
            "",
            "0x12345",
            "test",
            60,
            15,
            "0xowner",
            "ETH/USDT",
            "5m",
            "kraken",
        ),
        "0x67890": SubgraphFeed(
            "",
            "0x67890",
            "test",
            60,
            15,
            "0xowner",
            "ETH/DAI",
            "1h",
            "binanceus",
        ),
    }

    assert ss.get_feed_from_candidates(cand_feeds) == cand_feeds["0x12345"]
