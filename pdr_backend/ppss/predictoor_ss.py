from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import SingleFeedMixin
from pdr_backend.ppss.regressionmodel_ss import RegressionModelSS
from pdr_backend.ppss.classifiermodel_ss import ClassifierModelSS
from pdr_backend.util.strutil import StrMixin


class PredictoorSS(SingleFeedMixin, StrMixin):
    __STR_OBJDIR__ = ["d"]
    FEED_KEY = "predict_feed"

    @enforce_types
    def __init__(self, d: dict):
        super().__init__(d, assert_feed_attributes=["timeframe"])
        if "regressionmodel_ss" in d:
            self.regressionmodel_ss = RegressionModelSS(d["regressionmodel_ss"])
        if "classifiermodel_ss" in d:
            self.classifiermodel_ss = ClassifierModelSS(d["classifiermodel_ss"])
        if not "classifiermodel_ss" in d and not "regressionmodel_ss" in d:
            raise ValueError("No model provided")

    # --------------------------------
    # yaml properties

    # (predict_feed defined in base)

    @property
    def stake_amount(self) -> int:
        """
        @description
          How much your bot stakes. In OCEAN per epoch, per feed
        """
        return self.d["stake_amount"]

    @property
    def others_stake(self) -> int:
        """
        @description
          How much all others' bots stake.
          In OCEAN per epoch, per feed. Simulation only.
        """
        return self.d["sim_only"]["others_stake"]

    @property
    def others_accuracy(self) -> float:
        """
        @description
          What % of others' bots stake is correct?
          Returns a value in range [0.0, 1.0]
          Simulation only.
        """
        return self.d["sim_only"]["others_accuracy"]

    @property
    def revenue(self) -> float:
        """
        @description
          Sales revenue going towards predictoors.
          In OCEAN per epoch, per feed. Simulation only.
        """
        return self.d["sim_only"]["revenue"]

    @property
    def s_until_epoch_end(self) -> int:
        return self.d["bot_only"]["s_until_epoch_end"]

    @property
    def stake_amount(self) -> int:
        return self.d["bot_only"]["stake_amount"]

    @property
    def is_two_sided(self) -> bool:
        return self.d["is_two_sided"]

    # feed defined in base

    # --------------------------------
    # derivative properties
