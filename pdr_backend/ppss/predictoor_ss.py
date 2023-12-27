from enforce_typing import enforce_types
from typing import Dict, Union

from pdr_backend.util.strutil import StrMixin
from pdr_backend.ppss.aimodel_ss import AimodelSS
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_pair import ArgPair
from pdr_backend.cli.timeframe import Timeframe
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed


class PredictoorSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["predictor_ss"]
        self.aimodel_ss = AimodelSS(d["aimodel_ss"])

        ArgFeed.from_str(d["predict_feed"])  # validate
        Timeframe(d["timeframe"])  # validate

    # --------------------------------
    # yaml properties
    @property
    def s_until_epoch_end(self) -> int:
        return self.d["bot_only"]["s_until_epoch_end"]

    @property
    def stake_amount(self) -> int:
        return self.d["bot_only"]["stake_amount"]

    @property
    def predict_feed(self) -> ArgFeed:
        """Which feed to use for predictions. Eg "feed1"."""
        return ArgFeed.from_str(self.d["predict_feed"])

    @property
    def timeframe(self) -> str:
        return self.d["timeframe"]  # eg "1m"

    # --------------------------------
    # derivative properties
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
