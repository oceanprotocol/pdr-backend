from typing import Dict, List, Optional

from enforce_typing import enforce_types

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
    # yaml properties
    @property
    def predict_train_feedsets(self) -> PredictTrainFeedsets:
        feedset_list: List[dict] = self.d["predict_train_feedsets"]
        return PredictTrainFeedsets.from_list_of_dict(feedset_list)

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
        return self.d["bot_only"]["pred_submitter_mgr"]

    @property
    def min_payout_slots(self) -> int:
        if "min_payout_slots" not in self.d["bot_only"]:
            return 0
        return self.d["bot_only"]["min_payout_slots"]

    # --------------------------------
    # setters (add as needed)
    @enforce_types
    def set_approach(self, approach: int):
        if approach not in CAND_APPROACHES:
            s = f"Allowed approaches={CAND_APPROACHES}, got {self.approach}"
            raise ValueError(s)
        self.d["approach"] = approach

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
    pred_submitter_mgr="",
) -> dict:
    """Use this function's return dict 'd' to construct PredictoorSS(d)"""
    feedset_list = feedset_list or feedset_test_list()
    d = {
        "predict_train_feedsets": feedset_list,
        "approach": 1,
        "stake_amount": 1,
        "sim_only": {
            "others_stake": 2313,
            "others_accuracy": 0.50001,
            "revenue": 0.93007,
        },
        "bot_only": {
            "pred_submitter_mgr": pred_submitter_mgr,
            "s_until_epoch_end": 60,
            "s_start_payouts": 0,
        },
        "aimodel_ss": aimodel_ss_test_dict(),
    }
    return d
