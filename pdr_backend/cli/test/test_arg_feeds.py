import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds


@enforce_types
def test_ArgFeeds_from_str():
    # 1 feed
    target_feeds = [ArgFeed("binance", "open", "ADA/USDT")]
    assert ArgFeeds.from_str("binance ADA/USDT o") == target_feeds
    assert ArgFeeds.from_str("binance ADA-USDT o") == target_feeds

    # >1 signal, so >1 feed
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT"),
        ArgFeed("binance", "close", "ADA/USDT"),
    ]
    assert ArgFeeds.from_str("binance ADA/USDT oc") == target_feeds
    assert ArgFeeds.from_str("binance ADA-USDT oc") == target_feeds

    # >1 pair, so >1 feed
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT"),
        ArgFeed("binance", "open", "ETH/RAI"),
    ]
    assert ArgFeeds.from_str("binance ADA/USDT ETH/RAI o") == target_feeds
    assert ArgFeeds.from_str("binance ADA-USDT ETH/RAI o") == target_feeds
    assert ArgFeeds.from_str("binance ADA-USDT ETH-RAI o") == target_feeds

    # >1 signal and >1 pair, so >1 feed
    target = ArgFeeds(
        [
            ArgFeed("binance", "close", "ADA/USDT"),
            ArgFeed("binance", "close", "BTC/USDT"),
            ArgFeed("binance", "open", "ADA/USDT"),
            ArgFeed("binance", "open", "BTC/USDT"),
        ]
    )
    assert ArgFeeds.from_str("binance ADA/USDT,BTC/USDT oc") == target
    assert ArgFeeds.from_str("binance ADA-USDT,BTC/USDT oc") == target
    assert ArgFeeds.from_str("binance ADA-USDT,BTC-USDT oc") == target

    # >1 signal and >1 pair, so >1 feed
    target = ArgFeeds(
        [
            ArgFeed("binance", "close", "ADA/USDT", "1h"),
            ArgFeed("binance", "close", "ADA/USDT", "5m"),
            ArgFeed("binance", "close", "BTC/USDT", "1h"),
            ArgFeed("binance", "close", "BTC/USDT", "5m"),
            ArgFeed("binance", "open", "ADA/USDT", "1h"),
            ArgFeed("binance", "open", "ADA/USDT", "5m"),
            ArgFeed("binance", "open", "BTC/USDT", "1h"),
            ArgFeed("binance", "open", "BTC/USDT", "5m"),
        ]
    )
    assert ArgFeeds.from_str("binance ADA/USDT,BTC/USDT oc 1h,5m") == target

    # unhappy paths. Verify section has way more, this is just for baseline
    strs = [
        "xyz ADA/USDT o",
        "binance ADA/USDT ox",
        "binance ADA/X o",
    ]
    for feeds_str in strs:
        with pytest.raises(ValueError):
            ArgFeeds.from_str(feeds_str)

    targ_prs = set(["ADA/USDT", "BTC/USDT"])
    assert ArgFeeds.from_str("binance ADA/USDT BTC/USDT o").pairs == targ_prs
    assert ArgFeeds.from_str("binance ADA-USDT BTC/USDT o").pairs == targ_prs
    assert ArgFeeds.from_str("binance ADA-USDT BTC-USDT o").pairs == targ_prs

    targ_prs = set(["ADA/USDT", "BTC/USDT"])
    assert ArgFeeds.from_str("binance ADA/USDT,BTC/USDT oc").pairs == targ_prs
    assert ArgFeeds.from_str("binance ADA-USDT,BTC/USDT oc").pairs == targ_prs
    assert ArgFeeds.from_str("binance ADA-USDT,BTC-USDT oc").pairs == targ_prs

    targ_prs = set(["ADA/USDT", "BTC/USDT", "ETH/USDC", "DOT/DAI"])
    assert (
        ArgFeeds.from_str("binance ADA/USDT  BTC/USDT  ,ETH/USDC,    DOT/DAI oc").pairs
        == targ_prs
    )


@enforce_types
def test_ArgFeeds_from_strs_main():
    # 1 str w 1 feed, 1 feed total
    target_feeds = [ArgFeed("binance", "open", "ADA/USDT")]
    assert ArgFeeds.from_strs(["binance ADA/USDT o"]) == target_feeds
    assert ArgFeeds.from_strs(["binance ADA-USDT o"]) == target_feeds

    target_feeds = [ArgFeed("binance", "open", "ADA/USDT", "1h")]
    assert ArgFeeds.from_strs(["binance ADA-USDT o 1h"]) == target_feeds

    # 1 str w 2 feeds, 2 feeds total
    target_feeds = ArgFeeds(
        [
            ArgFeed("binance", "open", "ADA/USDT"),
            ArgFeed("binance", "high", "ADA/USDT"),
        ]
    )
    assert ArgFeeds.from_strs(["binance ADA/USDT oh"]) == target_feeds
    assert ArgFeeds.from_strs(["binance ADA-USDT oh"]) == target_feeds
    assert target_feeds.signals == set(["open", "high"])
    assert target_feeds.exchanges == set(["binance"])

    # 2 strs each w 1 feed, 2 feeds total
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT"),
        ArgFeed("kraken", "high", "ADA/RAI"),
    ]
    feeds = ArgFeeds.from_strs(
        [
            "binance ADA-USDT o",
            "kraken ADA/RAI h",
        ]
    )
    assert feeds == target_feeds

    # 2 strs each w 1 feed, 2 feeds total, with timeframes and without signals
    target_feeds = [
        ArgFeed("binance", None, "ADA/USDT", "5m"),
        ArgFeed("kraken", None, "ADA/RAI", "1h"),
    ]
    feeds = ArgFeeds.from_strs(
        [
            "binance ADA-USDT 5m",
            "kraken ADA/RAI 1h",
        ]
    )
    assert feeds == target_feeds

    # 2 strs each w 1 feed, with timeframes 3 feeds total
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT", "5m"),
        ArgFeed("binance", "open", "ADA/USDT", "1h"),
        ArgFeed("kraken", "high", "ADA/RAI", "1h"),
    ]
    feeds = ArgFeeds.from_strs(
        [
            "binance ADA-USDT o 5m,1h",
            "kraken ADA/RAI h 1h",
        ]
    )
    assert feeds == target_feeds

    # first str has 4 feeds and second has 1 feed; 5 feeds total
    target_feeds = ArgFeeds(
        [
            ArgFeed("binance", "close", "ADA/USDT"),
            ArgFeed("binance", "close", "BTC/USDT"),
            ArgFeed("binance", "open", "ADA/USDT"),
            ArgFeed("binance", "open", "BTC/USDT"),
            ArgFeed("kraken", "high", "ADA/RAI"),
        ]
    )
    feeds = ArgFeeds.from_strs(
        [
            "binance ADA-USDT BTC/USDT oc",
            "kraken ADA-RAI h",
        ]
    )
    assert feeds == target_feeds

    # unhappy paths. Note: verify section has way more
    lists = [
        [],
        ["xyz ADA/USDT o"],
        ["binance ADA/USDT ox"],
        ["binance ADA/X o"],
        ["binance ADA/X o 1h"],
        ["binance ADA/X o 1h 1d"],
        ["binance ADA/X o 10h"],
    ]
    for feeds_strs in lists:
        with pytest.raises(ValueError):
            ArgFeeds.from_strs(feeds_strs)


@enforce_types
def test_ArgFeeds_from_strs__many_inputs():
    # ok for verify_feeds_strs
    lists = [
        ["binance ADA/USDT o"],
        ["binance ADA-USDT o"],
        ["binance ADA/USDT BTC/USDT oc", "kraken ADA/RAI h"],
        ["binance ADA/USDT BTC-USDT oc", "kraken ADA/RAI h"],
        [
            "binance ADA/USDT BTC-USDT oc 1h,5m",
            "kraken ADA/RAI h 1h",
            "binance BTC/USDT o",
        ],
    ]
    for feeds_strs in lists:
        ArgFeeds.from_strs(feeds_strs)

    # not ok for verify_feeds_strs
    lists = [
        [],
        [""],
        ["kraken ADA/RAI xh"],
        ["binance ADA/USDT BTC/USDT xoc", "kraken ADA/RAI h"],
        ["binance ADA/USDT BTC/USDT xoc 1h", "kraken ADA/RAI 5m"],
        ["", "kraken ADA/RAI h"],
        ["", "kraken ADA/RAI h 5m"],
    ]
    for feeds_strs in lists:
        with pytest.raises(ValueError):
            ArgFeeds.from_strs(feeds_strs)


@enforce_types
def test_ArgFeeds_and_ArgFeed_from_str_many_inputs():
    # ok for verify_feeds_str, ok for verify_feed_str
    # (well-formed 1 signal and 1 pair)
    strs = [
        "binance ADA/USDT o",
        "binance ADA-USDT o",
        "   binance ADA/USDT o",
        "binance ADA/USDT o",
        "   binance ADA/USDT    o",
        "   binance     ADA/USDT    o      ",
        "binance ADA/USDT",
        "   binance ADA/USDT ",
        "   binance ADA/USDT    ",
        "   binance     ADA/USDT    ",
    ]
    for feed_str in strs:
        ArgFeeds.from_str(feed_str)
    for feeds_str in strs:
        ArgFeeds.from_str(feeds_str)

    # not ok for verify_feed_str, ok for verify_feeds_str
    # (well-formed >1 signal or >1 pair)
    strs = [
        "binance ADA/USDT oh",
        "binance ADA-USDT oh",
        "   binance ADA/USDT oh",
        "binance ADA/USDT BTC/USDT oh",
        "  binance ADA/USDT BTC/USDT   o",
        "binance ADA/USDT,   BTC/USDT   ,ETH/USDC  ,  DOT/DAI o",
        "    binance ADA/USDT,   BTC/USDT   ,ETH/USDC  ,  DOT/DAI   o",
        "    binance ADA/USDT,   BTC-USDT   ,ETH/USDC  ,  DOT/DAI   o",
    ]
    for feed_str in strs:
        with pytest.raises(ValueError):
            ArgFeed.from_str(feed_str)

    # not ok for verify_feed_str, not ok for verify_feeds_str
    # (poorly formed)
    strs = [
        "",
        "  ",
        ",",
        " , ",
        " , ,",
        "  xyz ",
        "  xyz abc  ",
        "binance o",
        "binance o ",
        "binance o ,",
        "o ADA/USDT",
        "binance,ADA/USDT",
        "binance,ADA-USDT",
        "xyz ADA/USDT o",  # catch non-exchanges!
        "binancexyz ADA/USDT o",
        "binance ADA/USDT ohx",
        "binance ADA/USDT z",
        "binance , ADA/USDT, o,",
        "binance , ADA-USDT, o, ",
        "binance,ADA/USDT,o",
        "binance XYZ o",
        "binance USDT o",
        "binance ADA/ o",
        "binance ADA- o",
        "binance /USDT o",
        "binance ADA:USDT o",
        "binance ADA::USDT o",
        "binance ADA,USDT o",
        "binance ADA&USDT o",
        "binance ADA/USDT XYZ o",
    ]

    for feed_str in strs:
        with pytest.raises(ValueError):
            ArgFeed.from_str(feed_str)

    for feeds_str in strs:
        with pytest.raises(ValueError):
            ArgFeed.from_str(feeds_str)


@enforce_types
def test_ArgFeeds_contains_combination_1():
    # feeds have no timeframe so contains all timeframes
    feeds = ArgFeeds(
        [ArgFeed("binance", "close", "BTC/USDT"), ArgFeed("kraken", "close", "BTC/DAI")]
    )

    assert feeds.contains_combination("binance", "BTC/USDT", "1h")
    assert feeds.contains_combination("kraken", "BTC/DAI", "5m")
    assert not feeds.contains_combination("kraken", "BTC/USDT", "1h")

    # binance feed has a timeframe so contains just those timeframes
    feeds = ArgFeeds(
        [
            ArgFeed("binance", "close", "BTC/USDT", "5m"),
            ArgFeed("kraken", "close", "BTC/DAI"),
        ]
    )

    assert not feeds.contains_combination("binance", "BTC/USDT", "1h")
    assert feeds.contains_combination("binance", "BTC/USDT", "5m")
    assert feeds.contains_combination("kraken", "BTC/DAI", "5m")
    assert feeds.contains_combination("kraken", "BTC/DAI", "1h")


@enforce_types
def test_ArgFeeds_str():
    feeds = ArgFeeds.from_strs(["binance BTC/USDT oh 5m"])
    assert str(feeds) == "binance BTC/USDT oh 5m"

    feeds = ArgFeeds.from_strs(["binance BTC/USDT oh 5m", "kraken BTC/USDT c"])
    assert str(feeds) == "binance BTC/USDT oh 5m, kraken BTC/USDT c"


@enforce_types
def test_ArgFeeds_to_strs1():
    for feeds_strs in [
        ["binance BTC/USDT o"],
        ["binance BTC/USDT oh"],
        ["binance BTC/USDT 5m"],
        ["binance BTC/USDT o 5m"],
        ["binance BTC/USDT oh 5m"],
        ["binance BTC/USDT ETH/USDT oh 5m"],
        ["binance BTC/USDT ohl 5m", "binance ETH/USDT ohlv 5m"],
        [
            "binance BTC/USDT ohl 5m",
            "binance ETH/USDT ohlv 5m",
            "binance DOT/USDT c 5m",
            "kraken BTC/USDT c",
        ],
    ]:
        feeds = ArgFeeds.from_strs(feeds_strs)
        assert sorted(feeds.to_strs()) == sorted(feeds_strs)
