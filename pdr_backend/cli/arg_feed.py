#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
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
from pdr_backend.cli.arg_vb import ArgVB, ArgVBs, vb_str_ok
from pdr_backend.cli.arg_tb import ArgTB, ArgTBs, tb_str_ok
from pdr_backend.cli.arg_db import ArgDB, ArgDBs, db_str_ok


class ArgFeed:
    def __init__(
        self,
        exchange: Union[ArgExchange, str],
        signal: Union[ArgSignal, str, None] = None,
        pair: Union[ArgPair, str, None] = None,
        timeframe: Optional[Union[ArgTimeframe, str]] = None,
        volume_threshold: Optional[Union[ArgVB, str]] = None,
        tick_threshold: Optional[Union[ArgTB, str]] = None,
        dollar_threshold: Optional[Union[ArgDB, str]] = None,
        contract: Optional[str] = None,
    ):
        if signal is not None:
            self.signal = ArgSignal(signal) if isinstance(signal, str) else signal

        if pair is None:
            raise ValueError("pair cannot be None")

        self.exchange: ArgExchange = (
            ArgExchange(exchange) if isinstance(exchange, str) else exchange
        )
        self.pair = ArgPair(pair) if isinstance(pair, str) else pair
        self.signal = ArgSignal(signal) if isinstance(signal, str) else signal

        if timeframe is None:
            self.timeframe = None
        elif isinstance(timeframe, str):
            self.timeframe = ArgTimeframe(timeframe)
        else:
            self.timeframe = timeframe

        if volume_threshold is None:
            self.volume_threshold = None
        elif isinstance(volume_threshold, str):
            self.volume_threshold = ArgVB(volume_threshold)
        else:
            self.volume_threshold = volume_threshold
        
        if dollar_threshold is None:
            self.dollar_threshold = None
        elif isinstance(dollar_threshold, str):
            self.dollar_threshold = ArgDB(dollar_threshold)
        else:
            self.dollar_threshold = dollar_threshold
        
        if tick_threshold is None:
            self.tick_threshold = None
        elif isinstance(tick_threshold, str):
            self.tick_threshold = ArgTB(tick_threshold)
        else:
            self.tick_threshold = tick_threshold

        self.contract = contract

    def __str__(self):
        feed_str = f"{self.exchange} {self.pair}"
        
        # feed_str = exchange + pair + signal + timeframe + volume + tick + dollar
        if self.signal is not None:
            char = self.signal.to_char()
            feed_str += f" {char}"

        if self.timeframe is not None:
            feed_str += f" {self.timeframe}"

        if self.volume_threshold is not None:
            feed_str += f" {self.volume_threshold}"
        
        if self.tick_threshold is not None:
            feed_str += f" {self.tick_threshold}"
        
        if self.dollar_threshold is not None:
            feed_str += f" {self.dollar_threshold}"

        return feed_str

    def __eq__(self, other) -> bool:
        assert isinstance(other, ArgFeed), (other, type(other))
        return (
            self.exchange == other.exchange
            and str(self.signal) == str(other.signal)
            and str(self.pair) == str(other.pair)
            and str(self.timeframe) == str(other.timeframe)
            and str(self.volume_threshold) == str(other.volume_threshold)
            and str(self.tick_threshold) == str(other.tick_threshold)
            and str(self.dollar_threshold) == str(other.dollar_threshold)
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
      volume_bar_feeds = "<exchange_str> <pairs_str> <volume_threshold> "
      dollar_bar_feeds = "<exchange_str> <pairs_str> <dollar_threshold> "
      ticks_bar_feeds = "<exchange_str> <pairs_str> <tick_threshold> "
      do_verify - typically T. Only F to avoid recursion from verify functions

    @return
      feed_tups - list of (exchange_str, signal_str, pair_str)
    """
    feeds_str = feeds_str.strip()
    feeds_str = " ".join(feeds_str.split())  # replace multiple whitespace w/ 1
    feeds_str_split = feeds_str.split(" ")

    exchange_str = feeds_str_split[0]

    threshold_str = feeds_str_split[-1]
    offset_end = None

    if vb_str_ok(threshold_str):
        # last part is a valid volume_threshold
        vb_str_list = ArgVBs.from_str(threshold_str)
        feeds_str_split = feeds_str_split[:-1]
        db_str_list = [None]
        tb_str_list = [None] 
    elif tb_str_ok(threshold_str):
        tb_str_list = ArgTBs.from_str(threshold_str)
        feeds_str_split = feeds_str_split[:-1]
        vb_str_list = [None]
        db_str_list = [None]
    elif db_str_ok(threshold_str):
        db_str_list = ArgDBs.from_str(threshold_str)
        feeds_str_split = feeds_str_split[:-1]
        vb_str_list = [None]
        tb_str_list = [None]
    else:
        vb_str_list = [None]
        db_str_list = [None]
        tb_str_list = [None]
        
    timeframe_str = feeds_str_split[-1]
    if timeframes_str_ok(timeframe_str):
        timeframe_str = feeds_str_split[-1]
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
        vb_str_list = [None]
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

    if isinstance(vb_str_list[0], ArgVB):
        if len(pairs) != len(vb_str_list):
            raise ValueError(
                "The lists 'pairs' and 'volume_thresholds' do not have the same length."
            )
        feeds = [
            ArgFeed(
                exchange_str, signal_str, pair_str, timeframe_str, volume_threshold_str
            )
            for signal_str in signal_str_list
            for pair_str, volume_threshold_str in zip(pairs, vb_str_list)
            for timeframe_str in timeframe_str_list
        ]
    elif isinstance(tb_str_list[0], ArgTB):
        if len(pairs) != len(tb_str_list):
            raise ValueError(
                "The lists 'pairs' and 'tick_thresholds' do not have the same length."
            )
        feeds = [
            ArgFeed(
                exchange_str, signal_str, pair_str, timeframe_str, tick_threshold=tick_threshold_str
            )
            for signal_str in signal_str_list
            for pair_str, tick_threshold_str in zip(pairs, tb_str_list)
            for timeframe_str in timeframe_str_list
        ]
    elif isinstance(db_str_list[0], ArgDB):
        if len(pairs) != len(db_str_list):
            raise ValueError(
                "The lists 'pairs' and 'dollar_thresholds' do not have the same length."
            )
        feeds = [
            ArgFeed(
                exchange_str, signal_str, pair_str, timeframe_str, dollar_threshold=dollar_threshold_str
            )
            for signal_str in signal_str_list
            for pair_str, dollar_threshold_str in zip(pairs, db_str_list)
            for timeframe_str in timeframe_str_list
        ]
    else:
        feeds = [
            ArgFeed(
                exchange_str, signal_str, pair_str, timeframe_str, volume_threshold_str
            )
            for signal_str in signal_str_list
            for pair_str in pairs
            for timeframe_str in timeframe_str_list
            for volume_threshold_str in vb_str_list
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
