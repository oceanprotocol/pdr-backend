from typing import Optional

from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import SingleFeedMixin
from pdr_backend.ppss.aimodel_ss import AimodelSS
from pdr_backend.util.strutil import StrMixin
from pdr_backend.util.currency_types import Eth

# Approaches:
#  1: Allocate up-vs-down stake equally (50-50). Baseline.
#  2: Allocate up-vs-down stake on model prediction confidence.
CAND_APPROACHES = [1, 2]


class PredictoorSS(SingleFeedMixin, StrMixin):
    __STR_OBJDIR__ = ["d"]
    FEED_KEY = "predict_feed"

    @enforce_types
    def __init__(self, d: dict):
        super().__init__(d, assert_feed_attributes=["timeframe"])
        self.aimodel_ss = AimodelSS(d["aimodel_ss"])
        if self.approach not in CAND_APPROACHES:
            s = f"Allowed approaches={CAND_APPROACHES}, got {self.approach}"
            raise ValueError(s)

    # --------------------------------
    # yaml properties

    # (predict_feed defined in base)

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
        if "s_start_payouts" in self.d["bot_only"]:
            return 0
        return self.d["bot_only"]["s_start_payouts"]

    @property
    def s_until_epoch_end(self) -> int:
        return self.d["bot_only"]["s_until_epoch_end"]

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
def predictoor_ss_test_dict(predict_feed: Optional[str] = None) -> dict:
    """Use this function's return dict 'd' to construct PredictoorSS(d)"""
    predict_feed = predict_feed or "binance BTC/USDT c 5m"
    input_feeds = [predict_feed]
    d = {
        "predict_feed": predict_feed,
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
        "aimodel_ss": {
            "input_feeds": input_feeds,
            "approach": "LinearLogistic",
            "max_n_train": 7,
            "autoregressive_n": 3,
        },
    }
    return d
