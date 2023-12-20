import pytest
from enforce_typing import enforce_types

from pdr_backend.util.feedstr import ArgFeed, ArgFeeds


@enforce_types
def test_unpack_feeds_strs():
    # 1 str w 1 feed, 1 feed total
    target_feeds = [ArgFeed("binance", "open", "ADA/USDT")]
    assert ArgFeeds.from_strs(["binance ADA/USDT o"]) == target_feeds
    assert ArgFeeds.from_strs(["binance ADA-USDT o"]) == target_feeds

    # 1 str w 2 feeds, 2 feeds total
    target_feeds = [
        ArgFeed("binance", "open", "ADA/USDT"),
        ArgFeed("binance", "high", "ADA/USDT"),
    ]
    assert ArgFeeds.from_strs(["binance ADA/USDT oh"]) == target_feeds
    assert ArgFeeds.from_strs(["binance ADA-USDT oh"]) == target_feeds

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
    ]
    for feeds_strs in lists:
        with pytest.raises(ValueError):
            ArgFeeds.from_strs(feeds_strs)


@enforce_types
def test_unpack_feeds_str():
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
def test_unpack_feed_str():
    target_feed = ArgFeed("binance", "close", "BTC/USDT")
    assert ArgFeed.from_str("binance BTC/USDT c") == target_feed
    assert ArgFeed.from_str("binance BTC-USDT c") == target_feed


# ==========================================================================
# pack..() functions


@enforce_types
def test_pack_feed_str():
    target_feed_str = "binance BTC/USDT o"
    assert str(ArgFeed("binance", "open", "BTC/USDT")) == target_feed_str
    assert str(ArgFeed("binance", "open", "BTC-USDT")) == target_feed_str


# ==========================================================================
# verify..() functions
@enforce_types
def test_verify_feeds_strs():
    # ok for verify_feeds_strs
    lists = [
        ["binance ADA/USDT o"],
        ["binance ADA-USDT o"],
        ["binance ADA/USDT BTC/USDT oc", "kraken ADA/RAI h"],
        ["binance ADA/USDT BTC-USDT oc", "kraken ADA/RAI h"],
    ]
    for feeds_strs in lists:
        ArgFeeds.from_strs(feeds_strs)

    # not ok for verify_feeds_strs
    lists = [
        [],
        [""],
        ["binance ADA/USDT BTC/USDT xoc", "kraken ADA/RAI h"],
        ["", "kraken ADA/RAI h"],
    ]
    for feeds_strs in lists:
        with pytest.raises(ValueError):
            ArgFeeds.from_strs(feeds_strs)


@enforce_types
def test_verify_feeds_str__and__verify_feed_str():
    # ok for verify_feeds_str, ok for verify_feed_str
    # (well-formed 1 signal and 1 pair)
    strs = [
        "binance ADA/USDT o",
        "binance ADA-USDT o",
        "   binance ADA/USDT o",
        "binance ADA/USDT o",
        "   binance ADA/USDT    o",
        "   binance     ADA/USDT    o      ",
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
        "binance ADA/USDT",
        "binance,ADA/USDT",
        "binance,ADA-USDT",
        "binance , ADA/USDT",
        "xyz ADA/USDT o",  # catch non-exchanges!
        "binancexyz ADA/USDT o",
        "binance ADA/USDT ohx",
        "binance ADA/USDT z",
        "binance , ADA/USDT o",
        "binance , ADA/USDT, o",
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
