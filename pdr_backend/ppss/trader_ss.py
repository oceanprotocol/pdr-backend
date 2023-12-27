from typing import Union

from enforce_typing import enforce_types
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_pair import ArgPair
from pdr_backend.cli.timeframe import Timeframe
from pdr_backend.util.strutil import StrMixin


class TraderSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["trader_ss"]
        ArgFeed.from_str(d["predict_feed"])  # validate
        Timeframe(d["timeframe"])  # validate

    # --------------------------------
    # yaml properties: sim only
    @property
    def buy_amt_str(self) -> Union[int, float]:
        """How much to buy. Eg 10."""
        return self.d["sim_only"]["buy_amt"]

    @property
    def predict_feed(self) -> str:
        """Which feed to use for predictions. Eg "feed1"."""
        return ArgFeed.from_str(self.d["predict_feed"])

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

    @property
    def timeframe(self) -> str:
        return self.d["timeframe"]  # eg "1m"

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
    def pair_str(self) -> ArgPair:
        """Return e.g. 'ETH/USDT'. Only applicable when 1 feed."""
        return self.predict_feed.pair

    @property
    def exchange_str(self) -> str:
        """Return e.g. 'binance'. Only applicable when 1 feed."""
        return str(self.predict_feed.exchange)

    @property
    def exchange_class(self) -> str:
        return self.predict_feed.exchange.exchange_class

    @property
    def signal_str(self) -> str:
        """Return e.g. 'high'. Only applicable when 1 feed."""
        return self.predict_feed.signal

    @property
    def base_str(self) -> str:
        """Return e.g. 'ETH'. Only applicable when 1 feed."""
        return ArgPair(self.pair_str).base_str or ""

    @property
    def quote_str(self) -> str:
        """Return e.g. 'USDT'. Only applicable when 1 feed."""
        return ArgPair(self.pair_str).quote_str or ""

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


# =========================================================================
# utilities for testing


@enforce_types
def inplace_make_trader_fast(trader_ss: TraderSS):
    trader_ss.set_max_tries(10)
    trader_ss.set_position_size(10.0)
    trader_ss.set_min_buffer(20)
