from typing import Dict, Union

from enforce_typing import enforce_types
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_pair import ArgPair
from pdr_backend.util.strutil import StrMixin
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed


class TraderSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["trader_ss"]
        feed = ArgFeed.from_str(d["predict_feed"])  # validate
        assert feed.timeframe

    # --------------------------------
    # yaml properties: sim only
    @property
    def buy_amt_str(self) -> Union[int, float]:
        """How much to buy. Eg 10."""
        return self.d["sim_only"]["buy_amt"]

    @property
    def predict_feed(self) -> ArgFeed:
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
    def timeframe(self) -> str:
        return str(self.predict_feed.timeframe)  # eg "1m"

    @property
    def timeframe_ms(self) -> int:
        """Returns timeframe, in ms"""
        return self.predict_feed.timeframe.ms

    @property
    def timeframe_s(self) -> int:
        """Returns timeframe, in s"""
        return self.predict_feed.timeframe.s

    @property
    def timeframe_m(self) -> int:
        """Returns timeframe, in minutes"""
        return self.predict_feed.timeframe.m

    @enforce_types
    def get_predict_feed_from_candidates(
        self, cand_feeds: Dict[str, SubgraphFeed]
    ) -> Union[None, SubgraphFeed]:
        allowed_tup = (
            self.timeframe,
            self.predict_feed.exchange,
            self.predict_feed.pair,
        )

        for feed in cand_feeds.values():
            assert isinstance(feed, SubgraphFeed)
            feed_tup = (feed.timeframe, feed.source, feed.pair)
            if feed_tup == allowed_tup:
                return feed

        return None


# =========================================================================
# utilities for testing


@enforce_types
def inplace_make_trader_fast(trader_ss: TraderSS):
    trader_ss.set_max_tries(10)
    trader_ss.set_position_size(10.0)
    trader_ss.set_min_buffer(20)
