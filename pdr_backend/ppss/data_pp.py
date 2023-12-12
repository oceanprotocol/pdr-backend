from typing import Dict, List, Tuple

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.models.feed import Feed
from pdr_backend.util.feedstr import unpack_feeds_strs, verify_feeds_strs
from pdr_backend.util.listutil import remove_dups
from pdr_backend.util.pairstr import unpack_pair_str
from pdr_backend.util.timeframestr import Timeframe, verify_timeframe_str


class DataPP:
    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["data_pp"]

        # test inputs
        verify_timeframe_str(self.timeframe)
        verify_feeds_strs(self.predict_feeds_strs)
        if not (0 < self.test_n < np.inf):  # pylint: disable=superfluous-parens
            raise ValueError(f"test_n={self.test_n}, must be >0 and <inf")

    # --------------------------------
    # yaml properties
    @property
    def timeframe(self) -> str:
        return self.d["timeframe"]  # eg "1m"

    @property
    def predict_feeds_strs(self) -> List[str]:
        return self.d["predict_feeds"]  # eg ["binance oh BTC/USDT",..]

    @property
    def test_n(self) -> int:
        return self.d["sim_only"]["test_n"]  # eg 200

    # --------------------------------
    # setters
    @enforce_types
    def set_timeframe(self, timeframe: str):
        self.d["timeframe"] = timeframe

    @enforce_types
    def set_predict_feeds(self, predict_feeds_strs: List[str]):
        self.d["predict_feeds"] = predict_feeds_strs

    # --------------------------------
    # derivative properties
    @property
    def timeframe_ms(self) -> int:
        """Returns timeframe, in ms"""
        return Timeframe(self.timeframe).ms

    @property
    def timeframe_s(self) -> int:
        """Returns timeframe, in s"""
        return Timeframe(self.timeframe).s

    @property
    def timeframe_m(self) -> int:
        """Returns timeframe, in minutes"""
        return Timeframe(self.timeframe).m

    @property
    def predict_feed_tups(self) -> List[Tuple[str, str, str]]:
        """
        Return list of (exchange_str, signal_str, pair_str)
        E.g. [("binance", "open",  "ADA/USDT"), ...]
        """
        return unpack_feeds_strs(self.predict_feeds_strs)

    @property
    def pair_strs(self) -> set:
        """Return e.g. ['ETH/USDT','BTC/USDT']."""
        return remove_dups([tup[2] for tup in self.predict_feed_tups])

    @property
    def exchange_strs(self) -> str:
        """Return e.g. ['binance','kraken']."""
        return remove_dups([tup[0] for tup in self.predict_feed_tups])

    @property
    def predict_feed_tup(self) -> Tuple[str, str, str]:
        """
        Return (exchange_str, signal_str, pair_str)
        E.g. ("binance", "open",  "ADA/USDT")
        Only applicable when 1 feed.
        """
        if len(self.predict_feed_tups) != 1:
            raise ValueError("This method only works with 1 predict_feed")
        return self.predict_feed_tups[0]

    @property
    def exchange_str(self) -> str:
        """Return e.g. 'binance'. Only applicable when 1 feed."""
        return self.predict_feed_tup[0]

    @property
    def signal_str(self) -> str:
        """Return e.g. 'high'. Only applicable when 1 feed."""
        return self.predict_feed_tup[1]

    @property
    def pair_str(self) -> str:
        """Return e.g. 'ETH/USDT'. Only applicable when 1 feed."""
        return self.predict_feed_tup[2]

    @property
    def base_str(self) -> str:
        """Return e.g. 'ETH'. Only applicable when 1 feed."""
        return unpack_pair_str(self.pair_str)[0]

    @property
    def quote_str(self) -> str:
        """Return e.g. 'USDT'. Only applicable when 1 feed."""
        return unpack_pair_str(self.pair_str)[1]

    @property
    def filter_feeds_s(self) -> str:
        """Return a string describing how feeds are filtered by,
        when using filter_feeds()"""
        return f"{self.timeframe} {self.predict_feeds_strs}"

    @enforce_types
    def filter_feeds(self, cand_feeds: Dict[str, Feed]) -> Dict[str, Feed]:
        """
        @description
          Filter to feeds that fit self.predict_feed_tups'
            (exchange_str, pair) combos

        @arguments
          cand_feeds -- dict of [feed_addr] : Feed

        @return
          final_feeds -- dict of [feed_addr] : Feed
        """
        allowed_tups = [
            (self.timeframe, exchange, pair)
            for exchange, _, pair in self.predict_feed_tups
        ]

        final_feeds: Dict[str, Feed] = {}
        found_tups = set()  # to avoid duplicates
        for feed in cand_feeds.values():
            assert isinstance(feed, Feed)
            feed_tup = (feed.timeframe, feed.source, feed.pair)
            if feed_tup in allowed_tups and feed_tup not in found_tups:
                final_feeds[feed.address] = feed
                found_tups.add(feed_tup)
        return final_feeds

    @enforce_types
    def __str__(self) -> str:
        s = "DataPP:\n"
        s += f"  timeframe={self.timeframe}\n"
        s += f"  predict_feeds_strs={self.predict_feeds_strs}\n"
        s += f"  test_n={self.test_n}\n"
        s += "-" * 10 + "\n"
        return s


@enforce_types
def mock_data_pp(timeframe_str: str, predict_feeds: List[str]) -> DataPP:
    data_pp = DataPP(
        {
            "timeframe": timeframe_str,
            "predict_feeds": predict_feeds,
            "sim_only": {"test_n": 2},
        }
    )
    return data_pp
