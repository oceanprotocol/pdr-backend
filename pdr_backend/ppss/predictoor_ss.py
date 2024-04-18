from typing import Dict, List, Optional

from enforce_typing import enforce_types

from pdr_backend.cli.arg_exchange import ArgExchange
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_pair import ArgPair
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.cli.predict_train_feedsets import (
    PredictTrainFeedset,
    PredictTrainFeedsets,
)
from pdr_backend.ppss.aimodel_ss import AimodelSS, aimodel_ss_test_dict
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.currency_types import Eth
from pdr_backend.util.strutil import StrMixin

# Approaches:
#  1: Two-sided: Allocate up-vs-down stake equally (50-50). Baseline.
#  2: Two-sided: Allocate up-vs-down stake on model prediction confidence.
#  3: One sided: If up, allocate 2's up-minus-down stake. If down, vice versa.
CAND_APPROACHES = [1, 2, 3]


class PredictoorSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d
        self.aimodel_ss = AimodelSS(d["aimodel_ss"])

        if self.approach not in CAND_APPROACHES:
            s = f"Allowed approaches={CAND_APPROACHES}, got {self.approach}"
            raise ValueError(s)

    # ------------------------------------------------------------------
    # yaml properties (except feeds-related attributes, see below for that)

    @property
    def approach(self) -> int:
        return self.d["approach"]

    @property
    def stake_amount(self) -> Eth:
        """
        @description
          Total bot stake amount, per epoch, per feed. In OCEAN.
        """
        return Eth(self.d["stake_amount"])

    @property
    def others_stake(self) -> Eth:
        """
        @description
          How much all others' bots stake. Per epoch, per feed. In OCEAN.
          Simulation only.
        """
        return Eth(self.d["sim_only"]["others_stake"])

    @property
    def others_accuracy(self) -> float:
        """
        @description
          What % of others' bots stake is correct? Return val in range [0.0,1.0]
          Simulation only.
        """
        return self.d["sim_only"]["others_accuracy"]

    @property
    def revenue(self) -> Eth:
        """
        @description
          Sales revenue going towards predictoors. Per epoch, per feed. OCEAN.
          Simulation only.
        """
        return Eth(self.d["sim_only"]["revenue"])

    @property
    def s_start_payouts(self) -> int:
        if "s_start_payouts" not in self.d["bot_only"]:
            return 0
        return self.d["bot_only"]["s_start_payouts"]

    @property
    def s_until_epoch_end(self) -> int:
        return self.d["bot_only"]["s_until_epoch_end"]

    @property
    def pred_submitter_mgr(self) -> str:
        return self.d["pred_submitter_mgr"]

    # ------------------------------------------------------------------
    # 'predict_train_feedsets' attribute and related

    @property
    def predict_train_feedsets(self) -> PredictTrainFeedsets:
        return PredictTrainFeedsets.from_array(self.d["predict_train_feedsets"])

    @property
    def minimum_timeframe_seconds(self) -> int:
        min_tf_seconds = int(1e9)
        for feed in self.predict_train_feedsets.feeds:
            assert feed.timeframe is not None, f"Feed: {feed} is missing timeframe"
            min_tf_seconds = min(min_tf_seconds, feed.timeframe.s)
        return min_tf_seconds

    @enforce_types
    def get_predict_train_feedset(
        self,
        pair: ArgPair,
        timeframe: Optional[ArgTimeframe],
        exchange: ArgExchange,
    ) -> Optional[PredictTrainFeedset]:

        for predict_train_feedset in self.predict_train_feedsets:
            predict_feed: ArgFeed = predict_train_feedset.predict
            if (
                predict_feed.pair == pair
                and predict_feed.timeframe == timeframe
                and predict_feed.exchange == exchange
            ):
                return predict_train_feedset

        return None

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

    # --------------------------------
    # setters (add as needed)
    @enforce_types
    def set_approach(self, approach: int):
        if approach not in CAND_APPROACHES:
            s = f"Allowed approaches={CAND_APPROACHES}, got {self.approach}"
            raise ValueError(s)
        self.d["approach"] = approach


# =========================================================================
# utilities for testing


@enforce_types
def feedset_test_list() -> list:
    return [
        {
            "predict": "binance BTC/USDT c 5m",
            "train_on": "binance BTC/USDT c 5m",
        },
        {
            "predict": "kraken ETH/USDT c 5m",
            "train_on": "kraken ETH/USDT c 5m",
        },
    ]


@enforce_types
def predictoor_ss_test_dict(
    feedset_list: Optional[List] = None,
    pred_submitter_mgr="",
) -> dict:
    """Use this function's return dict 'd' to construct PredictoorSS(d)"""
    feedset_list = feedset_list or feedset_test_list()
    d = {
        "predict_train_feedsets": feedset_list,
        "approach": 1,
        "stake_amount": 1,
        "pred_submitter_mgr": pred_submitter_mgr,
        "sim_only": {
            "others_stake": 2313,
            "others_accuracy": 0.50001,
            "revenue": 0.93007,
        },
        "bot_only": {
            "s_until_epoch_end": 60,
            "s_start_payouts": 0,
        },
        "aimodel_ss": aimodel_ss_test_dict(),
    }
    return d
