#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Dict, List, Optional, Set, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_exchange import ArgExchange
from pdr_backend.cli.arg_feed import (
    ArgFeed,
    _unpack_feeds_str,
    _pack_feeds_str,
)
from pdr_backend.cli.arg_pair import ArgPair
from pdr_backend.cli.arg_timeframe import ArgTimeframe


class ArgFeeds(List[ArgFeed]):
    @enforce_types
    def __init__(self, feeds: List[ArgFeed]):
        super().__init__(feeds)

    @staticmethod
    def from_str(feeds_str: str) -> "ArgFeeds":
        return ArgFeeds(_unpack_feeds_str(feeds_str))

    @staticmethod
    def from_strs(feeds_strs: List[str], do_verify: bool = True) -> "ArgFeeds":
        if do_verify:
            if not feeds_strs:
                raise ValueError(feeds_strs)

        feeds = []
        for feeds_str in feeds_strs:
            feeds += _unpack_feeds_str(str(feeds_str))

        return ArgFeeds(feeds)

    @property
    def pairs(self) -> Set[str]:
        return set(str(feed.pair) for feed in self)

    @property
    def exchanges(self) -> Set[str]:
        return set(str(feed.exchange) for feed in self)

    @property
    def signals(self) -> Set[str]:
        return set(str(feed.signal) for feed in self)

    @enforce_types
    def contains_combination(
        self,
        source: Union[str, ArgExchange],
        pair: Union[str, ArgPair],
        timeframe: Union[str, ArgTimeframe],
    ) -> bool:
        for feed in self:
            if (
                feed.exchange == source
                and feed.pair == pair
                and (not feed.timeframe or feed.timeframe == timeframe)
            ):
                return True

        return False

    @enforce_types
    def __eq__(self, other) -> bool:
        return sorted([str(f) for f in self]) == sorted([str(f) for f in other])

    @enforce_types
    def __str__(self) -> str:
        return ", ".join(self.to_strs())

    @enforce_types
    def to_strs(self) -> List[str]:
        return _pack_feeds_str(self[:])

    @staticmethod
    def from_table_data(table_data: Optional[List[Dict]]) -> "ArgFeeds":
        if not table_data:
            return ArgFeeds([])

        return ArgFeeds(
            [
                ArgFeed(
                    pair=row["pair"],
                    contract=row["contract"],
                    exchange=row["source"],
                    timeframe=row["timeframe"],
                )
                for row in table_data
            ]
        )
