from typing import List, Tuple

from enforce_typing import enforce_types
import numpy as np

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

    @enforce_types
    def __str__(self) -> str:
        s = "DataPP:\n"
        s += f"  timeframe={self.timeframe}\n"
        s += f"  predict_feeds_strs={self.predict_feeds_strs}\n"
        s += f"  test_n={self.test_n}\n"
        s += "-" * 10 + "\n"
        return s
