from typing import Dict, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_pair import ArgPair
from pdr_backend.ppss.aimodel_ss import AimodelSS
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.strutil import StrMixin


class PredictoorSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["predictor_ss"]
        self.aimodel_ss = AimodelSS(d["aimodel_ss"])

        feed = ArgFeed.from_str(d["predict_feed"])  # validate
        assert feed.timeframe

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
        return str(self.predict_feed.signal)

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
        return str(self.predict_feed.timeframe)

    @property
    def timeframe_ms(self) -> int:
        """Returns timeframe, in ms"""
        return self.predict_feed.timeframe.ms if self.predict_feed.timeframe else 0

    @property
    def timeframe_s(self) -> int:
        """Returns timeframe, in s"""
        return self.predict_feed.timeframe.s if self.predict_feed.timeframe else 0

    @property
    def timeframe_m(self) -> int:
        """Returns timeframe, in minutes"""
        return self.predict_feed.timeframe.m if self.predict_feed.timeframe else 0

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
