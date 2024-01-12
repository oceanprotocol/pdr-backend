from collections import defaultdict
from typing import List, Optional, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_exchange import ArgExchange
from pdr_backend.cli.arg_pair import ArgPair, ArgPairs
from pdr_backend.cli.timeframe import (
    Timeframe,
    Timeframes,
    verify_timeframes_str,
)
from pdr_backend.util.signalstr import (
    signal_to_char,
    signals_to_chars,
    verify_signal_str,
    unpack_signalchar_str,
    verify_signalchar_str,
)


class ArgFeed:
    def __init__(
        self,
        exchange,
        signal: Union[str, None] = None,
        pair: Union[ArgPair, str, None] = None,
        timeframe: Optional[Union[Timeframe, str]] = None,
    ):
        if signal is not None:
            verify_signal_str(signal)

        if pair is None:
            raise ValueError("pair cannot be None")

        self.exchange = ArgExchange(exchange) if isinstance(exchange, str) else exchange
        self.pair = ArgPair(pair) if isinstance(pair, str) else pair
        self.signal = signal

        if timeframe is None:
            self.timeframe = None
        else:
            self.timeframe = (
                Timeframe(timeframe) if isinstance(timeframe, str) else timeframe
            )

    def __str__(self):
        feed_str = f"{self.exchange} {self.pair}"

        if self.signal is not None:
            char = signal_to_char(self.signal)
            feed_str += f" {char}"

        if self.timeframe is not None:
            feed_str += f" {self.timeframe}"

        return feed_str

    def __eq__(self, other):
        return (
            self.exchange == other.exchange
            and self.signal == other.signal
            and str(self.pair) == str(other.pair)
            and str(self.timeframe) == str(other.timeframe)
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
      feeds_str - "<exchange_str> <pairs_str> <chars subset of "ohclv"> <timeframe> "
      do_verify - typically T. Only F to avoid recursion from verify functions

    @return
      feed_tups - list of (exchange_str, signal_str, pair_str)
    """
    feeds_str = feeds_str.strip()
    feeds_str = " ".join(feeds_str.split())  # replace multiple whitespace w/ 1
    feeds_str_split = feeds_str.split(" ")

    exchange_str = feeds_str_split[0]

    timeframe_str = feeds_str_split[-1]
    offset_end = None

    if verify_timeframes_str(timeframe_str):
        timeframe_str_list = Timeframes.from_str(timeframe_str)

        # last part is a valid timeframe, and we might have a signal before it
        signal_char_str = feeds_str_split[-2]

        if verify_signalchar_str(signal_char_str, True):
            # last part is a valid timeframe and we have a valid signal before it
            signal_str_list = unpack_signalchar_str(signal_char_str)
            offset_end = -2
        else:
            # last part is a valid timeframe, but there is no signal before it
            signal_str_list = [None]
            offset_end = -1
    else:
        # last part is not a valid timeframe, but it might be a signal
        timeframe_str_list = [None]
        signal_char_str = feeds_str_split[-1]

        if verify_signalchar_str(signal_char_str, True):
            # last part is a valid signal
            signal_str_list = unpack_signalchar_str(signal_char_str)
            offset_end = -1
        else:
            # last part is not a valid timeframe, nor a signal
            signal_str_list = [None]
            offset_end = None

    pairs_list_str = " ".join(feeds_str_split[1:offset_end])

    pairs = ArgPairs.from_str(pairs_list_str)

    feeds = [
        ArgFeed(exchange_str, signal_str, pair_str, timeframe_str)
        for signal_str in signal_str_list
        for pair_str in pairs
        for timeframe_str in timeframe_str_list
    ]

    return feeds


@enforce_types
def _pack_feeds_str(feeds: List[ArgFeed]) -> List[str]:
    """
    Returns eg set([
      "binance BTC/USDT ohl 5m",
      "binance ETH/USDT ohlv 5m",
      "binance DOT/USDT c 5m",
      "kraken BTC/USDT c",
    ])
    """
    # merge signals via dict
    grouped_signals = defaultdict(set)  # [(exch,pair,timeframe)] : signals
    for feed in feeds:
        tup3 = (str(feed.exchange), str(feed.pair), str(feed.timeframe))
        if tup3 not in grouped_signals:
            grouped_signals[tup3] = {str(feed.signal)}
        else:
            grouped_signals[tup3].add(str(feed.signal))

    # convert new dict to list of 4-tups. Sort for consistency
    tup4s = []
    for (exch, pair, timeframe), signals in grouped_signals.items():
        signals = frozenset(sorted(signals))
        tup4s.append((exch, pair, timeframe, signals))
    tup4s = sorted(tup4s)

    # then, merge pairs via dic
    grouped_pairs = defaultdict(set)  # [(exch,timeframe,signals)] : pairs
    for exch, pair, timeframe, signals in tup4s:
        tup3 = (exch, timeframe, signals)
        if tup3 not in grouped_pairs:
            grouped_pairs[tup3] = {pair}
        else:
            grouped_pairs[tup3].add(pair)

    # convert new dict to list of 4-tups. Sort for consistency
    tup4s = []
    for (exch, timeframe, signals), pairs in grouped_pairs.items():
        pairs = frozenset(sorted(pairs))
        tup4s.append((exch, timeframe, signals, pairs))
    tup4s = sorted(tup4s)

    # convert to list of str
    strs = []
    for exch, timeframe, signals, pairs in tup4s:
        s = exch
        s += " " + " ".join(sorted(pairs))
        if signals != frozenset({"None"}):
            s += " " + signals_to_chars(signals)
        if timeframe != "None":
            s += " " + timeframe
        strs.append(s)

    return strs
