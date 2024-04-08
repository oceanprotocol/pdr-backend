from typing import Dict, List, Optional
from enforce_typing import enforce_types
from pdr_backend.cli.predict_feeds import PredictFeed, PredictFeeds
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed


@enforce_types
class PredictFeedMixin:
    FEEDS_KEY = "feeds"

    def __init__(self, d: dict, assert_feed_attributes: Optional[List] = None):
        assert self.__class__.FEEDS_KEY
        self.d = d
        if assert_feed_attributes:
            missing_attributes = []
            for attr in assert_feed_attributes:
                for feed in self.feeds.feeds:
                    if not getattr(feed, attr):
                        missing_attributes.append(attr)

            if missing_attributes:
                raise AssertionError(
                    f"Missing attributes {missing_attributes} for some feeds."
                )

    @property
    def feeds(self) -> PredictFeeds:
        return PredictFeeds.from_array(self.d.get(self.__class__.FEEDS_KEY, []))

    @property
    def minimum_timeframe_seconds(self) -> int:
        return min([feed.predict.timeframe.s for feed in self.feeds])

    def get_predict_feed(self, pair, timeframe, exchange) -> PredictFeed:
        for predict_feed in self.feeds:
            p = predict_feed.predict
            if p.pair == pair and p.timeframe == timeframe and p.exchange == exchange:
                return predict_feed
        return None

    @enforce_types
    def filter_feeds_from_candidates(
        self, cand_feeds: Dict[str, SubgraphFeed]
    ) -> Dict[str, SubgraphFeed]:
        result: Dict[str, SubgraphFeed] = {}

        allowed_tups = [
            (str(feed.exchange), str(feed.pair), str(feed.timeframe))
            for feed in self.feeds.feeds
        ]

        for sg_key, sg_feed in cand_feeds.items():
            assert isinstance(sg_feed, SubgraphFeed)

            if (sg_feed.source, sg_feed.pair, sg_feed.timeframe) in allowed_tups:
                result[sg_key] = sg_feed

        return result
