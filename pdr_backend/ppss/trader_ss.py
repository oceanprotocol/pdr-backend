from typing import Dict, List, Union

from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import SingleFeedMixin
from pdr_backend.util.strutil import StrMixin


class TraderSS(SingleFeedMixin, StrMixin):
    __STR_OBJDIR__ = ["d"]
    FEED_KEY = "feed"

    @enforce_types
    def __init__(self, d: dict):
        super().__init__(
            d, assert_feed_attributes=["timeframe"]
        )  # yaml_dict["trader_ss"]

    # --------------------------------
    # yaml properties: xpmt only
    @property
    def buy_amt_str(self) -> Union[int, float]:
        """How much to buy. Eg 10."""
        return self.d["xpmt_only"]["buy_amt"]

    @property
    def fee_percent(self) -> str:
        return self.d["xpmt_only"]["fee_percent"]  # Eg 0.001 is 0.1%.Trading fee

    @property
    def init_holdings_strs(self) -> List[str]:
        return self.d["xpmt_only"]["init_holdings"]  # eg ["1000 USDT", ..]

    @property
    def tradetype(self) -> str:
        return self.d.get("tradetype", "livemock")

    @property
    def allowed_tradetypes(self) -> List[str]:
        return ["livemock", "livereal"]

    # feed defined in base

    # --------------------------------
    # yaml properties: bot only
    @property
    def min_buffer(self) -> int:
        """Only trade if there's > this time left. Denominated in s."""
        return self.d["bot_only"]["min_buffer"]

    @property
    def max_tries(self) -> int:
        """Max no. attempts to process a feed. Eg 10"""
        return self.d["bot_only"]["max_tries"]

    @property
    def position_size(self) -> Union[int, float]:
        """Trading size. Eg 10"""
        return self.d["bot_only"]["position_size"]

    # --------------------------------
    # setters (add as needed)
    @enforce_types
    def set_max_tries(self, max_tries):
        self.d["bot_only"]["max_tries"] = max_tries

    @enforce_types
    def set_min_buffer(self, min_buffer):
        self.d["bot_only"]["min_buffer"] = min_buffer

    @enforce_types
    def set_position_size(self, position_size):
        self.d["bot_only"]["position_size"] = position_size

    # --------------------------------
    # derivative properties
    @property
    def buy_amt_usd(self):
        amt_s, _ = self.buy_amt_str.split()
        return float(amt_s)

    @property
    def init_holdings(self) -> Dict[str, float]:
        d = {}
        for s in self.init_holdings_strs:
            amt_s, coin = s.split()
            amt = float(amt_s)
            d[coin] = amt
        return d


# =========================================================================
# utilities for testing


@enforce_types
def inplace_make_trader_fast(trader_ss: TraderSS):
    trader_ss.set_max_tries(10)
    trader_ss.set_position_size(10.0)
    trader_ss.set_min_buffer(20)
