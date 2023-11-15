from typing import List, Tuple

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.util.constants import CAND_TIMEFRAMES
from pdr_backend.util.feedstr import unpack_feeds_strs, verify_feeds_strs
from pdr_backend.util.pairstr import unpack_pair_str
from pdr_backend.util.strutil import StrMixin


class DataPP(StrMixin):

    @enforce_types
    def __init__(self, d: dict):
        self.d = d # yaml_dict["data_pp"]

        # test inputs
        if self.timeframe not in CAND_TIMEFRAMES:
            raise ValueError(self.timeframe)
        verify_feeds_strs(self.predict_feeds_strs)
        assert 0 < self.test_n < np.inf

    # --------------------------------
    # yaml properties
    @property
    def timeframe(self) -> str:
        return self.d["timeframe"] # eg "1m"

    @property
    def predict_feeds_strs(self) -> List[str]:
        return self.d["predict_feeds"] # eg ["binance oh BTC/USDT",..]

    @property
    def test_n(self) -> int:
        return self.d["sim_only"]["test_n"] # eg 200

    # --------------------------------
    # derivative properties
    @property
    def timeframe_ms(self) -> int:
        """Returns timeframe, in ms"""
        return self.timeframe_m * 60 * 1000
    
    @property
    def timeframe_s(self) -> int:
        """Returns timeframe, in s"""
        return self.timeframe_m * 60

    @property
    def timeframe_m(self) -> int:
        """Returns timeframe, in minutes"""
        if self.timeframe == "5m":
            return 5
        if self.timeframe == "1h":
            return 60
        raise ValueError("need to support timeframe={self.timeframe}")

    @property
    def predict_feed_tups(self) -> List[Tuple[str, str, str]]:
        """
        Return list of (exchange_str, signal_str, pair_str)
        E.g. [("binance", "open",  "ADA-USDT"), ...]
        """
        return unpack_feeds_strs(self.predict_feeds_strs)

    @property
    def predict_feed_tup(self) -> Tuple[str, str, str]:
        """
        Return (exchange_str, signal_str, pair_str)
        E.g. ("binance", "open",  "ADA-USDT")
        Only applicable when 1 feed.
        """
        assert len(self.predict_feed_tups) == 1
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
