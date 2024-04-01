from typing import Optional

from enforce_typing import enforce_types
from pdr_backend.cli.predict_feeds import PredictFeeds

from pdr_backend.ppss.aimodel_ss import AimodelSS, aimodel_ss_test_dict
from pdr_backend.ppss.predict_feed_mixin import PredictFeedMixin
from pdr_backend.util.strutil import StrMixin
from pdr_backend.util.currency_types import Eth

# Approaches:
#  1: Allocate up-vs-down stake equally (50-50). Baseline.
#  2: Allocate up-vs-down stake on model prediction confidence.
CAND_APPROACHES = [1, 2]


class PredictoorSS(PredictFeedMixin, StrMixin):
    __STR_OBJDIR__ = ["d"]
    FEEDS_KEY = "feeds"

    @enforce_types
    def __init__(self, d: dict):
        super().__init__(d, assert_feed_attributes=["timeframe"])
        self.aimodel_ss = AimodelSS(d["aimodel_ss"])
        if self.approach not in CAND_APPROACHES:
            s = f"Allowed approaches={CAND_APPROACHES}, got {self.approach}"
            raise ValueError(s)

    # --------------------------------
    # yaml properties

    # (predict_feeds defined in base)

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

    @property
    def s_cutoff(self) -> int:
        if "s_cutoff" not in self.d["bot_only"]:
            return 10
        return self.d["bot_only"]["s_cutoff"]

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


def example_predict_feeds() -> list:
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
    predict_feeds: Optional[PredictFeeds] = None,
    input_feeds: Optional[PredictFeeds] = None,
) -> dict:
    """Use this function's return dict 'd' to construct PredictoorSS(d)"""
    predict_feeds = predict_feeds or PredictFeeds.from_array(example_predict_feeds())
    input_feeds = input_feeds or predict_feeds.feeds_str
    print(predict_feeds, input_feeds)
    d = {
        "feeds": predict_feeds.to_list(),
        "approach": 1,
        "stake_amount": 1,
        "sim_only": {
            "others_stake": 2313,
            "others_accuracy": 0.50001,
            "revenue": 0.93007,
        },
        "bot_only": {
            "s_until_epoch_end": 60,
        },
        "aimodel_ss": aimodel_ss_test_dict(input_feeds),
    }
    return d
