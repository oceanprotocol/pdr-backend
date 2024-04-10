from collections import defaultdict
from typing import List, Optional, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_exchange import ArgExchange
from pdr_backend.cli.arg_pair import ArgPair, ArgPairs
from pdr_backend.cli.arg_signal import ArgSignal, ArgSignals, verify_signalchar_str
from pdr_backend.cli.arg_timeframe import (
    ArgTimeframe,
    ArgTimeframes,
    timeframes_str_ok,
)


class ArgFeed:
    def __init__(
        self,
        exchange,
        signal: Union[ArgSignal, str, None] = None,
        pair: Union[ArgPair, str, None] = None,
        timeframe: Optional[Union[ArgTimeframe, str]] = None,
    ):
        if signal is not None:
            self.signal = ArgSignal(signal) if isinstance(signal, str) else signal

        if pair is None:
            raise ValueError("pair cannot be None")

        self.exchange = ArgExchange(exchange) if isinstance(exchange, str) else exchange
        self.pair = ArgPair(pair) if isinstance(pair, str) else pair
        self.signal = ArgSignal(signal) if isinstance(signal, str) else signal

        if timeframe is None:
            self.timeframe = None
        else:
            self.timeframe = (
                ArgTimeframe(timeframe) if isinstance(timeframe, str) else timeframe
            )

    def __str__(self):
        feed_str = f"{self.exchange} {self.pair}"

        if self.signal is not None:
            char = self.signal.to_char()
            feed_str += f" {char}"

        if self.timeframe is not None:
            feed_str += f" {self.timeframe}"

        return feed_str

    def __eq__(self, other):
        return (
            self.exchange == other.exchange
            and str(self.signal) == str(other.signal)
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

    if timeframes_str_ok(timeframe_str):
        timeframe_str_list = ArgTimeframes.from_str(timeframe_str)

        # last part is a valid timeframe, and we might have a signal before it
        signal_char_str = feeds_str_split[-2]

        if verify_signalchar_str(signal_char_str, True):
            # last part is a valid timeframe and we have a valid signal before it
            signal_str_list = ArgSignals.from_str(signal_char_str)
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
            signal_str_list = ArgSignals.from_str(signal_char_str)
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
        ept_tup = (str(feed.exchange), str(feed.pair), str(feed.timeframe))
        if ept_tup not in grouped_signals:
            grouped_signals[ept_tup] = {str(feed.signal)}
        else:
            grouped_signals[ept_tup].add(str(feed.signal))

    # convert new dict to list of 4-tups. Sort for consistency
    epts_tups = []
    for (exch, pair, timeframe), signalset in grouped_signals.items():
        fr_signalset = frozenset(sorted(signalset))
        epts_tups.append((exch, pair, timeframe, fr_signalset))
    epts_tups = sorted(epts_tups)

    # then, merge pairs via dic
    grouped_pairs = defaultdict(set)  # [(exch,timeframe,signals)] : pairs
    for exch, pair, timeframe, fr_signalset in epts_tups:
        ets_tup = (exch, timeframe, fr_signalset)
        if ets_tup not in grouped_pairs:
            grouped_pairs[ets_tup] = {pair}
        else:
            grouped_pairs[ets_tup].add(pair)

    # convert new dict to list of 4-tups. Sort for consistency
    etsp_tups = []
    for (exch, timeframe, fr_signalset), pairs in grouped_pairs.items():
        fr_pairs = frozenset(sorted(pairs))
        etsp_tups.append((exch, timeframe, fr_signalset, fr_pairs))
    etsp_tups = sorted(etsp_tups)

    # convert to list of str
    strs = []
    for exch, timeframe, fr_signalset, fr_pairs in etsp_tups:
        s = exch
        s += " " + " ".join(sorted(fr_pairs))
        if fr_signalset != frozenset({"None"}):
            s += " " + ArgSignals(list(fr_signalset)).to_chars()
        if timeframe != "None":
            s += " " + timeframe
        strs.append(s)

    return strs
