from typing import Set

from enforce_typing import enforce_types
import pytest

from pdr_backend.util.feedstr import (
    unpack_feeds_strs,
    unpack_feeds_str,
    unpack_feed_str,
    pack_feed_str,
    verify_feeds_strs,
    verify_feeds_str,
    verify_feed_str,
    verify_feed_tup,
)


# ==========================================================================
# unpack..() functions


@enforce_types
def test_unpack_feeds_strs():
    # 1 str w 1 feed, 1 feed total
    target_feed_tups = [("binance", "open", "ADA/USDT")]
    assert unpack_feeds_strs(["binance o ADA/USDT"]) == target_feed_tups
    assert unpack_feeds_strs(["binance o ADA-USDT"]) == target_feed_tups

    # 1 str w 2 feeds, 2 feeds total
    target_feed_tups = [
        ("binance", "open", "ADA/USDT"),
        ("binance", "high", "ADA/USDT"),
    ]
    assert unpack_feeds_strs(["binance oh ADA/USDT"]) == target_feed_tups
    assert unpack_feeds_strs(["binance oh ADA-USDT"]) == target_feed_tups

    # 2 strs each w 1 feed, 2 feeds total
    target_feed_tups = [
        ("binance", "open", "ADA/USDT"),
        ("kraken", "high", "ADA/RAI"),
    ]
    feed_tups = unpack_feeds_strs(
        [
            "binance o ADA-USDT",
            "kraken h ADA/RAI",
        ]
    )
    assert feed_tups == target_feed_tups

    # first str has 4 feeds and second has 1 feed; 5 feeds total
    target_feed_tups = [
        ("binance", "close", "ADA/USDT"),
        ("binance", "close", "BTC/USDT"),
        ("binance", "open", "ADA/USDT"),
        ("binance", "open", "BTC/USDT"),
        ("kraken", "high", "ADA/RAI"),
    ]
    feed_tups = unpack_feeds_strs(
        [
            "binance oc ADA-USDT BTC/USDT",
            "kraken h ADA-RAI",
        ]
    )
    assert sorted(feed_tups) == target_feed_tups

    # unhappy paths. Note: verify section has way more
    lists = [
        [],
        ["xyz o ADA/USDT"],
        ["binance ox ADA/USDT"],
        ["binance o ADA/X"],
    ]
    for feeds_strs in lists:
        with pytest.raises(ValueError):
            unpack_feeds_strs(feeds_strs)


@enforce_types
def test_unpack_feeds_str():
    # 1 feed
    target_feed_tups = [("binance", "open", "ADA/USDT")]
    assert unpack_feeds_str("binance o ADA/USDT") == target_feed_tups
    assert unpack_feeds_str("binance o ADA-USDT") == target_feed_tups

    # >1 signal, so >1 feed
    target_feed_tups = [
        ("binance", "open", "ADA/USDT"),
        ("binance", "close", "ADA/USDT"),
    ]
    assert unpack_feeds_str("binance oc ADA/USDT") == target_feed_tups
    assert unpack_feeds_str("binance oc ADA-USDT") == target_feed_tups

    # >1 pair, so >1 feed
    target_feed_tups = [
        ("binance", "open", "ADA/USDT"),
        ("binance", "open", "ETH/RAI"),
    ]
    assert unpack_feeds_str("binance o ADA/USDT ETH/RAI") == target_feed_tups
    assert unpack_feeds_str("binance o ADA-USDT ETH/RAI") == target_feed_tups
    assert unpack_feeds_str("binance o ADA-USDT ETH-RAI") == target_feed_tups

    # >1 signal and >1 pair, so >1 feed
    target = [
        ("binance", "close", "ADA/USDT"),
        ("binance", "close", "BTC/USDT"),
        ("binance", "open", "ADA/USDT"),
        ("binance", "open", "BTC/USDT"),
    ]
    assert sorted(unpack_feeds_str("binance oc ADA/USDT,BTC/USDT")) == target
    assert sorted(unpack_feeds_str("binance oc ADA-USDT,BTC/USDT")) == target
    assert sorted(unpack_feeds_str("binance oc ADA-USDT,BTC-USDT")) == target

    # unhappy paths. Verify section has way more, this is just for baseline
    strs = [
        "xyz o ADA/USDT",
        "binance ox ADA/USDT",
        "binance o ADA/X",
    ]
    for feeds_str in strs:
        with pytest.raises(ValueError):
            unpack_feeds_str(feeds_str)

    # test separators between pairs: space, comma, both or a mix
    # Note: verify section has way more
    def _pairs(feed_tups) -> Set[str]:
        return set(pair for (_, _, pair) in feed_tups)

    targ_prs = set(["ADA/USDT", "BTC/USDT"])
    assert _pairs(unpack_feeds_str("binance o ADA/USDT BTC/USDT")) == targ_prs
    assert _pairs(unpack_feeds_str("binance o ADA-USDT BTC/USDT")) == targ_prs
    assert _pairs(unpack_feeds_str("binance o ADA-USDT BTC-USDT")) == targ_prs

    targ_prs = set(["ADA/USDT", "BTC/USDT"])
    assert _pairs(unpack_feeds_str("binance oc ADA/USDT,BTC/USDT")) == targ_prs
    assert _pairs(unpack_feeds_str("binance oc ADA-USDT,BTC/USDT")) == targ_prs
    assert _pairs(unpack_feeds_str("binance oc ADA-USDT,BTC-USDT")) == targ_prs

    targ_prs = set(["ADA/USDT", "BTC/USDT", "ETH/USDC", "DOT/DAI"])
    assert (
        _pairs(unpack_feeds_str("binance oc ADA/USDT  BTC/USDT  ,ETH/USDC,    DOT/DAI"))
        == targ_prs
    )


@enforce_types
def test_unpack_feed_str():
    target_feed_tup = ("binance", "close", "BTC/USDT")
    assert unpack_feed_str("binance c BTC/USDT") == target_feed_tup
    assert unpack_feed_str("binance c BTC-USDT") == target_feed_tup


# ==========================================================================
# pack..() functions


@enforce_types
def test_pack_feed_str():
    target_feed_str = "binance o BTC/USDT"
    assert pack_feed_str(("binance", "open", "BTC/USDT")) == target_feed_str
    assert pack_feed_str(("binance", "open", "BTC-USDT")) == target_feed_str


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
        verify_feeds_strs(feeds_strs)

    # not ok for verify_feeds_strs
    lists = [
        [],
        [""],
        ["binance xoc ADA/USDT BTC/USDT", "kraken h ADA/RAI"],
        ["", "kraken h ADA/RAI"],
    ]
    for feeds_strs in lists:
        with pytest.raises(ValueError):
            verify_feeds_strs(feeds_strs)


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
        verify_feed_str(feed_str)
    for feeds_str in strs:
        verify_feeds_str(feeds_str)

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
            verify_feed_str(feed_str)
    for feeds_str in strs:
        verify_feeds_str(feeds_str)

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
            verify_feed_str(feed_str)

    for feeds_str in strs:
        with pytest.raises(ValueError):
            verify_feeds_str(feeds_str)


@enforce_types
def test_verify_feed_tup():
    # ok
    tups = [
        ("binance", "open", "BTC/USDT"),
        ("kraken", "close", "BTC/DAI"),
        ("kraken", "close", "BTC-DAI"),
    ]
    for feed_tup in tups:
        verify_feed_tup(feed_tup)

    # not ok
    tups = [
        (),
        ("binance", "open"),
        ("binance", "open", ""),
        ("xyz", "open", "BTC/USDT"),
        ("xyz", "open", "BTC-USDT"),
        ("binance", "xyz", "BTC/USDT"),
        ("binance", "open", "BTC/XYZ"),
        ("binance", "open", "BTC/USDT", ""),
    ]
    for feed_tup in tups:
        with pytest.raises(ValueError):
            verify_feed_tup(feed_tup)
