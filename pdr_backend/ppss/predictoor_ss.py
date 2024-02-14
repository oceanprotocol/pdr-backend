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
        self.classifiermodel_ss = RegressionModelSS(d["regressionmodel_ss"])
        self.classifiermodel_ss = ClassifierModelSS(d["classifiermodel_ss"])

    # --------------------------------
    # yaml properties
    @property
    def s_until_epoch_end(self) -> int:
        return self.d["bot_only"]["s_until_epoch_end"]

    @property
    def stake_amount(self) -> int:
        return self.d["bot_only"]["stake_amount"]

    # feed defined in base

    # --------------------------------
    # derivative properties
