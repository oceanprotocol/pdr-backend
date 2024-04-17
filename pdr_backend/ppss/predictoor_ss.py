from typing import Dict, List, Optional

from enforce_typing import enforce_types

from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset, PredictFeeds
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
    # yaml properties (except 'feeds' attribute, see below for that)

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
    # 'feeds' attribute and related

    @property
    def feeds(self) -> PredictTrainFeedsets:
        return PredictTrainFeedsets.from_array(self.d["feeds"])

    @property
    def minimum_timeframe_seconds(self) -> int:
        min_tf_seconds = int(1e9)
        for feed in self.feeds:
            assert (
                feed.predict.timeframe is not None
            ), f"Feed: {feed} is missing timeframe"
            min_tf_seconds = min(min_tf_seconds, feed.predict.timeframe.s)
        return min_tf_seconds

    @enforce_types
    def get_predict_train_feedset(self, pair, timeframe, exchange) -> Optional[PredictTrainFeedset]:        
        for predict_train_feedset in self.predict_train_feedsets:
            predict_feed: ArgFeed = predict_train_feedset.predict
            if predict_feed.pair == pair and \
               predict_feed.timeframe == timeframe and \
               predict_feed.exchange == exchange:
                return feed
        return None

    @enforce_types
    def get_feed_from_candidates(
        self, cand_feeds: Dict[str, SubgraphFeed]
    ) -> Dict[str, SubgraphFeed]:
        """
        @description
          Return a set of feeds as the intersection of
          (1) candidate feeds read from chain, ie the input SubgraphFeeds; and
          (2) self's feeds to predict, ie input by PPSS
        """
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
def test_feedset_list() -> list:
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
    predict_train_feedsets: Optional[List] = None,
    pred_submitter_mgr="",
) -> dict:
    """Use this function's return dict 'd' to construct PredictoorSS(d)"""
    predict_train_feedsets = predict_feeds or test_feedset_list()
    d = {
        "feeds": predict_train_feedsets,
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
        },
        "aimodel_ss": aimodel_ss_test_dict(),
    }
    return d
