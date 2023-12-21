"""Utilities for all feeds from binance etc.
Used as inputs for models, and for predicing.
Complementary to subgraph/subgraph_feed.py which models a prediction feed contract.
"""

from typing import List, Set, Union

from enforce_typing import enforce_types

from pdr_backend.util.exchangestr import verify_exchange_str
from pdr_backend.util.signalstr import (
    signal_to_char,
    unpack_signalchar_str,
    verify_signal_str,
)
from pdr_backend.cli.arg_pair import ArgPair, ArgPairs


class ArgFeed:
    def __init__(self, exchange, signal, pair: Union[ArgPair, str]):
        verify_exchange_str(exchange)
        verify_signal_str(signal)

        self.exchange = exchange
        self.pair = ArgPair(pair) if isinstance(pair, str) else pair
        self.signal = signal

    def __str__(self):
        char = signal_to_char(self.signal)
        feed_str = f"{self.exchange} {self.pair} {char}"

        return feed_str

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            self.exchange == other.exchange
            and self.signal == other.signal
            and str(self.pair) == str(other.pair)
        )

    def __hash__(self):
        return hash((self.exchange, self.signal, str(self.pair)))

    @staticmethod
    def from_str(feed_str: str, do_verify: bool = True) -> "ArgFeed":
        """
        @description
          Unpack the string for a *single* feed: 1 exchange, 1 signal, 1 pair

          Example: Given "binance ADA-USDT o"
          Return Feed("binance", "open", "BTC/USDT")

        @argument
          feed_str -- eg "binance ADA/USDT o"; not eg "binance oc ADA/USDT BTC/DAI"
          do_verify - typically T. Only F to avoid recursion from verify functions

        @return
          Feed
        """
        feeds_str = feed_str
        feeds = _unpack_feeds_str(feeds_str)

        if do_verify:
            if len(feeds) != 1:
                raise ValueError(feed_str)
        feed = feeds[0]
        return feed


class ArgFeeds(List[ArgFeed]):
    @staticmethod
    def from_strs(feeds_strs: List[str], do_verify: bool = True) -> "ArgFeeds":
        if do_verify:
            if not feeds_strs:
                raise ValueError(feeds_strs)

        feeds = []
        for feeds_str in feeds_strs:
            feeds += _unpack_feeds_str(feeds_str)

        return ArgFeeds(feeds)

    def __init__(self, feeds: List[ArgFeed]):
        super().__init__(feeds)

    @staticmethod
    def from_str(feeds_str: str) -> "ArgFeeds":
        return ArgFeeds(_unpack_feeds_str(feeds_str))

    def __eq__(self, other):
        intersection = set(self).intersection(set(other))
        return len(intersection) == len(self) and len(intersection) == len(other)

    @property
    def pairs(self) -> Set[str]:
        return set(str(feed.pair) for feed in self)

    @property
    def exchanges(self) -> Set[str]:
        return set(feed.exchange for feed in self)

    @property
    def signals(self) -> Set[str]:
        return set(feed.signal for feed in self)


@enforce_types
def _unpack_feeds_str(feeds_str: str) -> List[ArgFeed]:
    """
    @description
      Unpack a *single* feeds str. It can have >1 feeds of course.

      Example: Given "binance oc ADA/USDT BTC-USDT"
      Return [
          ("binance", "open",  "ADA/USDT"),
          ("binance", "close", "ADA/USDT"),
          ("binance", "open",  "BTC/USDT"),
          ("binance", "close", "BTC/USDT"),
      ]

    @arguments
      feeds_str - "<exchange_str> <chars subset of "ohclv"> <pairs_str>"
      do_verify - typically T. Only F to avoid recursion from verify functions

    @return
      feed_tups - list of (exchange_str, signal_str, pair_str)
    """
    feeds_str = feeds_str.strip()
    feeds_str = " ".join(feeds_str.split())  # replace multiple whitespace w/ 1
    feeds_str_split = feeds_str.split(" ")

    if len(feeds_str_split) < 3:
        # TODO: this will be adapted to support missing signal
        raise ValueError(feeds_str)

    exchange_str = feeds_str_split[0]
    pairs_list_str = " ".join(feeds_str_split[1:-1])
    signal_char_str = feeds_str_split[-1]

    signal_str_list = unpack_signalchar_str(signal_char_str)
    pairs = ArgPairs.from_str(pairs_list_str)

    feeds = [
        ArgFeed(exchange_str, signal_str, pair_str)
        for signal_str in signal_str_list
        for pair_str in pairs
    ]

    return feeds
