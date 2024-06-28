#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
from typing import Dict, List, Optional, Set, Tuple, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.arg_pair import ArgPair
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed


class MultiFeedMixin:
    FEEDS_KEY = ""

    @enforce_types
    def __init__(self, d: dict, assert_feed_attributes: Optional[List] = None):
        assert self.__class__.FEEDS_KEY
        self.d = d
        feeds = ArgFeeds.from_strs(self.feeds_strs)

        if assert_feed_attributes:
            missing_attributes = []
            for attr in assert_feed_attributes:
                for feed in feeds:
                    if not getattr(feed, attr):
                        missing_attributes.append(attr)

            if missing_attributes:
                raise AssertionError(
                    f"Missing attributes {missing_attributes} for some feeds."
                )

    # --------------------------------
    # yaml properties
    @property
    def feeds_strs(self) -> List[str]:
        nested_attrs = self.__class__.FEEDS_KEY.split(".")
        lookup = copy.deepcopy(self.d)

        # Iterate over each attribute in the nesting
        for attr in nested_attrs:
            try:
                # Attempt to access the next level in the dict
                lookup = lookup[attr]
            except KeyError as exc:
                raise ValueError(
                    f"Could not find nested attribute {attr} in {nested_attrs}"
                ) from exc

        assert isinstance(lookup, list)
        return lookup  # eg ["binance BTC/USDT ohlcv",..]

    # --------------------------------

    @property
    def n_exchs(self) -> int:
        return len(self.exchange_strs)

    @property
    def exchange_strs(self) -> Set[str]:
        return set(str(feed.exchange) for feed in self.feeds)

    @property
    def n_feeds(self) -> int:
        return len(self.feeds)

    @property
    def feeds(self) -> ArgFeeds:
        """Return list of ArgFeed(exchange_str, signal_str, pair_str)"""
        return ArgFeeds.from_strs(self.feeds_strs)

    @property
    def exchange_pair_tups(self) -> Set[Tuple[str, str]]:
        """Return set of unique (exchange_str, pair_str) tuples"""
        return set((str(feed.exchange), str(feed.pair)) for feed in self.feeds)

    @enforce_types
    def filter_feeds_from_candidates(
        self, cand_feeds: Dict[str, SubgraphFeed]
    ) -> Dict[str, SubgraphFeed]:
        result: Dict[str, SubgraphFeed] = {}

        allowed_tups = [
            (str(feed.exchange), str(feed.pair), str(feed.timeframe))
            for feed in self.feeds
        ]

        for sg_key, sg_feed in cand_feeds.items():
            assert isinstance(sg_feed, SubgraphFeed)

            if (sg_feed.source, sg_feed.pair, sg_feed.timeframe) in allowed_tups:
                result[sg_key] = sg_feed

        return result


class SingleFeedMixin:
    FEED_KEY = ""

    @enforce_types
    def __init__(self, d: dict, assert_feed_attributes: Optional[List] = None):
        assert self.__class__.FEED_KEY
        self.d = d
        if assert_feed_attributes:
            for attr in assert_feed_attributes:
                assert getattr(self.feed, attr)

        if hasattr(self, "tradetype"):
            assert hasattr(self, "allowed_tradetypes")
            if self.tradetype not in self.allowed_tradetypes:
                raise ValueError(
                    f"{self.tradetype} not in allowed tradetypes "
                    f"{', '.join(self.allowed_tradetypes)}"
                )

    # --------------------------------
    # yaml properties
    @property
    def feed(self) -> ArgFeed:
        """Which feed to use for predictions. Eg "feed1"."""
        return ArgFeed.from_str(self.d[self.__class__.FEED_KEY])

    # --------------------------------

    @property
    def pair_str(self) -> str:
        """Return e.g. 'ETH/USDT'. Only applicable when 1 feed."""
        return str(self.feed.pair)

    @property
    def exchange_str(self) -> str:
        """Return e.g. 'binance'. Only applicable when 1 feed."""
        return str(self.feed.exchange)

    @property
    def signal_str(self) -> str:
        """Return e.g. 'high'. Only applicable when 1 feed."""
        return str(self.feed.signal) if self.feed.signal else ""

    @property
    def base_str(self) -> str:
        """Return e.g. 'ETH'. Only applicable when 1 feed."""
        return ArgPair(self.pair_str).base_str or ""

    @property
    def quote_str(self) -> str:
        """Return e.g. 'USDT'. Only applicable when 1 feed."""
        return ArgPair(self.pair_str).quote_str or ""

    @property
    def timeframe_str(self) -> str:
        return str(self.feed.timeframe)

    @property
    def timeframe_ms(self) -> int:
        """Returns timeframe, in ms"""
        return self.feed.timeframe.ms if self.feed.timeframe else 0

    @property
    def timeframe_s(self) -> int:
        """Returns timeframe, in s"""
        return self.feed.timeframe.s if self.feed.timeframe else 0

    @property
    def timeframe_m(self) -> int:
        """Returns timeframe, in minutes"""
        return self.feed.timeframe.m if self.feed.timeframe else 0

    @enforce_types
    def get_feed_from_candidates(
        self, cand_feeds: Dict[str, SubgraphFeed]
    ) -> Union[None, SubgraphFeed]:
        allowed_tup = (
            self.timeframe_str,
            str(self.feed.exchange),
            self.feed.pair,
        )

        for feed in cand_feeds.values():
            assert isinstance(feed, SubgraphFeed)
            feed_tup = (feed.timeframe, feed.source, feed.pair)
            if feed_tup == allowed_tup:
                return feed

        return None
