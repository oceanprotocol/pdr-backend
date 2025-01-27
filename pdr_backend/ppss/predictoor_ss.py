from typing import Dict, List, Optional

from enforce_typing import enforce_types

from pdr_backend.cli.predict_train_feedsets import (
    PredictTrainFeedset,
    PredictTrainFeedsets,
)
from pdr_backend.ppss.aimodel_data_ss import (
    AimodelDataSS,
    aimodel_data_ss_test_dict,
)
from pdr_backend.ppss.aimodel_ss import (
    AimodelSS,
    aimodel_ss_test_dict,
)
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.strutil import StrMixin


class PredictoorSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d
        self.aimodel_data_ss = AimodelDataSS(d["aimodel_data_ss"])
        self.aimodel_ss = AimodelSS(d["aimodel_ss"])

    # ------------------------------------------------------------------
    # yaml properties
    @property
    def predict_train_feedsets(self) -> PredictTrainFeedsets:
        feedset_list: List[dict] = self.d["predict_train_feedsets"]
        return PredictTrainFeedsets.from_list_of_dict(feedset_list)

    # ------------------------------------------------------------------
    # 'predict_train_feedsets' workers
    @enforce_types
    def get_predict_train_feedset(
        self,
        exchange_str: str,
        pair_str: str,
        timeframe_str: str,
    ) -> Optional[PredictTrainFeedset]:
        """Eg return a feedset given ("binance", "BTC/USDT", "5m" """
        return self.predict_train_feedsets.get_feedset(
            exchange_str,
            pair_str,
            timeframe_str,
        )

    @enforce_types
    def get_feed_from_candidates(
        self,
        cand_feeds: Dict[str, SubgraphFeed],
    ) -> Dict[str, SubgraphFeed]:
        """
        @description
          Filter down the input cand_feeds to the ones we're supposed to predict

          More precisely: return a set of feeds as the intersection of
          (1) candidate feeds read from chain, ie the input SubgraphFeeds,
          and (2) self's feeds to predict, ie input by PPSS

        @arguments
          cand_feeds -- dict of [feed_addr] : SubgraphFeed

        @return
          filtered_feeds -- dict of [feed_addr] : SubgraphFeed
        """
        filtered_feeds: Dict[str, SubgraphFeed] = {}

        allowed_tups = [
            (str(feed.exchange), str(feed.pair), str(feed.timeframe))
            for feed in self.predict_train_feedsets.feeds
        ]

        for feed_addr, feed in cand_feeds.items():
            assert isinstance(feed, SubgraphFeed)

            if (feed.source, feed.pair, feed.timeframe) in allowed_tups:
                filtered_feeds[feed_addr] = feed

        return filtered_feeds


# =========================================================================
# utilities for testing


@enforce_types
def feedset_test_list() -> list:
    feedset_list = [
        {
            "predict": "binance BTC/USDT c 5m",
            "train_on": "binance BTC/USDT c 5m",
        },
        {
            "predict": "kraken ETH/USDT c 5m",
            "train_on": "kraken ETH/USDT c 5m",
        },
    ]
    return feedset_list


@enforce_types
def predictoor_ss_test_dict(
    feedset_list: Optional[List] = None,
    aimodel_data_ss_dict: Optional[dict] = None,
    aimodel_ss_dict: Optional[dict] = None,
) -> dict:
    """Use this function's return dict 'd' to construct PredictoorSS(d)"""
    feedset_list = feedset_list or feedset_test_list()
    d = {
        "predict_train_feedsets": feedset_list,
        "aimodel_data_ss": aimodel_data_ss_dict or aimodel_data_ss_test_dict(),
        "aimodel_ss": aimodel_ss_dict or aimodel_ss_test_dict(),
    }
    return d
