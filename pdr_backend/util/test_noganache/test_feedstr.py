import pytest
from enforce_typing import enforce_types

from pdr_backend.util.feedstr import ArgFeed, ArgFeeds


@enforce_types
def test_unpack_feeds_strs():
    # 1 str w 1 feed, 1 feed total
    target_feeds = [ArgFeed("binance", "open", "ADA/USDT")]
    assert ArgFeeds.from_strs(["binance o ADA/USDT"]) == target_feeds
    assert ArgFeeds.from_strs(["binance o ADA-USDT"]) == target_feeds

    # 1 str w 2 feeds, 2 feeds total
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT"),
        ArgFeed("binance", "high", "ADA/USDT"),
    ]
    assert ArgFeeds.from_strs(["binance oh ADA/USDT"]) == target_feeds
    assert ArgFeeds.from_strs(["binance oh ADA-USDT"]) == target_feeds

    # 2 strs each w 1 feed, 2 feeds total
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT"),
        ArgFeed("kraken", "high", "ADA/RAI"),
    ]
    feeds = ArgFeeds.from_strs(
        [
            "binance o ADA-USDT",
            "kraken h ADA/RAI",
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
            "binance oc ADA-USDT BTC/USDT",
            "kraken h ADA-RAI",
        ]
    )
    assert feeds == target_feeds

    # unhappy paths. Note: verify section has way more
    lists = [
        [],
        ["xyz o ADA/USDT"],
        ["binance ox ADA/USDT"],
        ["binance o ADA/X"],
    ]
    for feeds_strs in lists:
        with pytest.raises(ValueError):
            ArgFeeds.from_strs(feeds_strs)


@enforce_types
def test_unpack_feeds_str():
    # 1 feed
    target_feeds = [ArgFeed("binance", "open", "ADA/USDT")]
    assert ArgFeeds.from_str("binance o ADA/USDT") == target_feeds
    assert ArgFeeds.from_str("binance o ADA-USDT") == target_feeds

    # >1 signal, so >1 feed
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT"),
        ArgFeed("binance", "close", "ADA/USDT"),
    ]
    assert ArgFeeds.from_str("binance oc ADA/USDT") == target_feeds
    assert ArgFeeds.from_str("binance oc ADA-USDT") == target_feeds

    # >1 pair, so >1 feed
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT"),
        ArgFeed("binance", "open", "ETH/RAI"),
    ]
    assert ArgFeeds.from_str("binance o ADA/USDT ETH/RAI") == target_feeds
    assert ArgFeeds.from_str("binance o ADA-USDT ETH/RAI") == target_feeds
    assert ArgFeeds.from_str("binance o ADA-USDT ETH-RAI") == target_feeds

    # >1 signal and >1 pair, so >1 feed
    target = ArgFeeds(
        [
            ArgFeed("binance", "close", "ADA/USDT"),
            ArgFeed("binance", "close", "BTC/USDT"),
            ArgFeed("binance", "open", "ADA/USDT"),
            ArgFeed("binance", "open", "BTC/USDT"),
        ]
    )
    assert ArgFeeds.from_str("binance oc ADA/USDT,BTC/USDT") == target
    assert ArgFeeds.from_str("binance oc ADA-USDT,BTC/USDT") == target
    assert ArgFeeds.from_str("binance oc ADA-USDT,BTC-USDT") == target

    # unhappy paths. Verify section has way more, this is just for baseline
    strs = [
        "xyz o ADA/USDT",
        "binance ox ADA/USDT",
        "binance o ADA/X",
    ]
    for feeds_str in strs:
        with pytest.raises(ValueError):
            ArgFeeds.from_str(feeds_str)

    targ_prs = set(["ADA/USDT", "BTC/USDT"])
    assert ArgFeeds.from_str("binance o ADA/USDT BTC/USDT").pairs == targ_prs
    assert ArgFeeds.from_str("binance o ADA-USDT BTC/USDT").pairs == targ_prs
    assert ArgFeeds.from_str("binance o ADA-USDT BTC-USDT").pairs == targ_prs

    targ_prs = set(["ADA/USDT", "BTC/USDT"])
    assert ArgFeeds.from_str("binance oc ADA/USDT,BTC/USDT").pairs == targ_prs
    assert ArgFeeds.from_str("binance oc ADA-USDT,BTC/USDT").pairs == targ_prs
    assert ArgFeeds.from_str("binance oc ADA-USDT,BTC-USDT").pairs == targ_prs

    targ_prs = set(["ADA/USDT", "BTC/USDT", "ETH/USDC", "DOT/DAI"])
    assert (
        ArgFeeds.from_str("binance oc ADA/USDT  BTC/USDT  ,ETH/USDC,    DOT/DAI").pairs
        == targ_prs
    )


@enforce_types
def test_unpack_feed_str():
    target_feed = ArgFeed("binance", "close", "BTC/USDT")
    assert ArgFeed.from_str("binance c BTC/USDT") == target_feed
    assert ArgFeed.from_str("binance c BTC-USDT") == target_feed


# ==========================================================================
# pack..() functions


@enforce_types
def test_pack_feed_str():
    target_feed_str = "binance o BTC/USDT"
    assert str(ArgFeed("binance", "open", "BTC/USDT")) == target_feed_str
    assert str(ArgFeed("binance", "open", "BTC-USDT")) == target_feed_str


# ==========================================================================
# verify..() functions
@enforce_types
def test_verify_feeds_strs():
    # ok for verify_feeds_strs
    lists = [
        ["binance o ADA/USDT"],
        ["binance o ADA-USDT"],
        ["binance oc ADA/USDT BTC/USDT", "kraken h ADA/RAI"],
        ["binance oc ADA/USDT BTC-USDT", "kraken h ADA/RAI"],
    ]
    for feeds_strs in lists:
        ArgFeeds.from_strs(feeds_strs)

    # not ok for verify_feeds_strs
    lists = [
        [],
        [""],
        ["binance xoc ADA/USDT BTC/USDT", "kraken h ADA/RAI"],
        ["", "kraken h ADA/RAI"],
    ]
    for feeds_strs in lists:
        with pytest.raises(ValueError):
            ArgFeeds.from_strs(feeds_strs)


@enforce_types
def test_verify_feeds_str__and__verify_feed_str():
    # ok for verify_feeds_str, ok for verify_feed_str
    # (well-formed 1 signal and 1 pair)
    strs = [
        "binance o ADA/USDT",
        "binance o ADA-USDT",
        "   binance o ADA/USDT",
        "binance o ADA/USDT",
        "   binance o ADA/USDT    ",
        "   binance     o      ADA/USDT    ",
    ]
    for feed_str in strs:
        ArgFeeds.from_str(feed_str)
    for feeds_str in strs:
        ArgFeeds.from_str(feeds_str)

    # not ok for verify_feed_str, ok for verify_feeds_str
    # (well-formed >1 signal or >1 pair)
    strs = [
        "binance oh ADA/USDT",
        "binance oh ADA-USDT",
        "   binance oh ADA/USDT",
        "binance o ADA/USDT BTC/USDT",
        "  binance o   ADA/USDT BTC/USDT   ",
        "binance o ADA/USDT,   BTC/USDT   ,ETH/USDC  ,  DOT/DAI",
        "    binance o ADA/USDT,   BTC/USDT   ,ETH/USDC  ,  DOT/DAI   ",
        "    binance o ADA/USDT,   BTC-USDT   ,ETH/USDC  ,  DOT/DAI   ",
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
        "binance ADA/USDT",
        "binance,ADA/USDT",
        "binance,ADA-USDT",
        "binance , ADA/USDT",
        "xyz o ADA/USDT",  # catch non-exchanges!
        "binancexyz o ADA/USDT",
        "binance ohz ADA/USDT",
        "binance z ADA/USDT",
        "binance , o ADA/USDT",
        "binance o , ADA/USDT",
        "binance , o , ADA/USDT",
        "binance , o , ADA-USDT",
        "binance,o,ADA/USDT",
        "binance o XYZ",
        "binance o USDT",
        "binance o ADA/",
        "binance o ADA-",
        "binance o /USDT",
        "binance o ADA:USDT",
        "binance o ADA::USDT",
        "binance o ADA,USDT",
        "binance o ADA&USDT",
        "binance o ADA/USDT XYZ",
    ]
    for feed_str in strs:
        with pytest.raises(ValueError):
            ArgFeed.from_str(feed_str)

    for feeds_str in strs:
        with pytest.raises(ValueError):
            ArgFeed.from_str(feeds_str)


@enforce_types
def test_verify_ArgFeed():
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
    ]
    for feed_tup in tups:
        with pytest.raises(ValueError):
            ArgFeed(*feed_tup)

    # not ok - Type Error
    tups = [
        (),
        ("binance", "open"),
        ("binance", "open", "BTC/USDT", ""),
    ]
    for feed_tup in tups:
        with pytest.raises(TypeError):
            ArgFeed(*feed_tup)
