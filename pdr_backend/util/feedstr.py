"""Utilities for all feeds from binance etc.
Used as inputs for models, and for predicing.
Complementary to models/feed.py which models a prediction feed contract.
"""

from typing import List, Tuple

import ccxt
from enforce_typing import enforce_types

from pdr_backend.util.pairstr import (
    unpack_pairs_str,
    verify_pair_str,
)
from pdr_backend.util.signalstr import (
    signal_to_char,
    unpack_signalchar_str,
    verify_signal_str,
)

# ==========================================================================
# unpack..() functions


@enforce_types
def unpack_feeds_strs(
    feeds_strs: List[str], do_verify: bool = True
) -> List[Tuple[str, List[str], List[str]]]:
    """
    @description
      Unpack *one or more* feeds strs.

      Example: Given [
        "binance oc ADA/USDT BTC/USDT",
        "kraken o BTC-USDT",
      ]
      Return [
          ("binance", "open",  "ADA-USDT"),
          ("binance", "close", "ADA-USDT"),
          ("binance", "open",  "BTC-USDT"),
          ("binance", "close", "BTC-USDT"),
          ("kraken", "open", "BTC-USDT"),
       ]

    @arguments
      feeds_strs - list of "<exchange_str> <chars subset of "ohclv"> <pairs_str>"
      do_verify - typically T. Only F to avoid recursion from verify functions

    @return
      feed_tups - list of (exchange_str, signal_str, pair_str)
    """
    if do_verify:
        if not feeds_strs:
            raise ValueError(feeds_strs)

    feed_tups = []
    for feeds_str in feeds_strs:
        feed_tups += unpack_feeds_str(feeds_str, do_verify=False)

    if do_verify:
        for feed_tup in feed_tups:
            verify_feed_tup(feed_tup)
    return feed_tups


@enforce_types
def unpack_feeds_str(
    feeds_str: str, do_verify: bool = True
) -> List[Tuple[str, str, str]]:
    """
    @description
      Unpack a *single* feeds str. It can have >1 feeds of course.

      Example: Given "binance oc ADA/USDT BTC/USDT"
      Return [
          ("binance", "open",  "ADA-USDT"),
          ("binance", "close", "ADA-USDT"),
          ("binance", "open",  "BTC-USDT"),
          ("binance", "close", "BTC-USDT"),
      ]

    @arguments
      feeds_str - "<exchange_str> <chars subset of "ohclv"> <pairs_str>"
      do_verify - typically T. Only F to avoid recursion from verify functions

    @return
      feed_tups - list of (exchange_str, signal_str, pair_str)
    """
    feeds_str = feeds_str.strip()
    feeds_str = " ".join(feeds_str.split())  # replace multiple whitespace w/ 1
    exchange_str, signal_char_str, pairs_str = feeds_str.split(" ", maxsplit=2)
    signal_str_list = unpack_signalchar_str(signal_char_str)
    pair_str_list = unpack_pairs_str(pairs_str)
    feed_tups = [
        (exchange_str, signal_str, pair_str)
        for signal_str in signal_str_list
        for pair_str in pair_str_list
    ]

    if do_verify:
        for feed_tup in feed_tups:
            verify_feed_tup(feed_tup)
    return feed_tups


@enforce_types
def unpack_feed_str(feed_str: str, do_verify: bool = True) -> Tuple[str, str, str]:
    """
    @description
      Unpack the string for a *single* feed: 1 exchange, 1 signal, 1 pair

      Example: Given "binance o ADA/USDT"
      Return ("binance", "open", "BTC-USDT")

    @argument
      feed_str -- eg "binance o ADA/USDT"; not eg "binance oc ADA/USDT BTC/DAI"
      do_verify - typically T. Only F to avoid recursion from verify functions

    @return
      feed_tup - (exchange_str, signal_str, pair_str)
    """
    feeds_str = feed_str
    feed_tups = unpack_feeds_str(feeds_str, do_verify=False)
    if do_verify:
        if len(feed_tups) != 1:
            raise ValueError(feed_str)
    feed_tup = feed_tups[0]
    return feed_tup


@enforce_types
def pack_feed_str(feed_tup: Tuple[str, str, str]) -> str:
    """
    Example: Given ("binance", "open", "BTC-USDT")
    Return "binance o ADA/USDT"
    """
    exchange_str, signal_str, pair_str = feed_tup
    char = signal_to_char(signal_str)
    feed_str = f"{exchange_str} {char} {pair_str}"
    return feed_str
    

# ==========================================================================
# verify..() functions


@enforce_types
def verify_feeds_strs(feeds_strs: List[str]):
    """
    @description
      Raise an error if feeds_strs is invalid

    @argument
      feeds_strs -- eg ["binance oh ADA/USDT BTC/USDT", "kraken o ADA/DAI"]
    """
    if not feeds_strs:
        raise ValueError()
    for feeds_str in feeds_strs:
        verify_feeds_str(feeds_str)


@enforce_types
def verify_feeds_str(feeds_str: str):
    """
    @description
      Raise an error if feeds_str is invalid

    @argument
      feeds_str -- e.g. "binance oh ADA/USDT BTC/USDT"
    """
    feed_tups = unpack_feeds_str(feeds_str, do_verify=False)
    if not feed_tups:
        raise ValueError(feeds_str)
    for feed_tup in feed_tups:
        verify_feed_tup(feed_tup)


@enforce_types
def verify_feed_str(feed_str: str):
    """
    @description
      Raise an error if feed_str is invalid

    @argument
      feed_str -- e.g. "binance o ADA/USDT"
    """
    feeds_str = feed_str
    feed_tups = unpack_feeds_str(feeds_str, do_verify=False)
    if not len(feed_tups) == 1:
        raise ValueError(feed_str)
    verify_feed_tup(feed_tups[0])


@enforce_types
def verify_feed_tup(feed_tup: Tuple[str, str, str]):
    """
    @description
      Raise an error if feed_tup is invalid.

    @argument
      feed_tup -- (exchange_str, signal_str, pair_str)
                  E.g. ("binance", "open", "BTC/USDT")
    """
    exchange_str, signal_str, pair_str = feed_tup
    verify_exchange_str(exchange_str)
    verify_signal_str(signal_str)
    verify_pair_str(pair_str)


@enforce_types
def verify_exchange_str(exchange_str: str):
    """
    @description
      Raise an error if exchange is invalid.

    @argument
      exchange_str -- e.g. "binance"
    """
    # it's valid if ccxt sees it
    if not hasattr(ccxt, exchange_str):
        raise ValueError(exchange_str)
