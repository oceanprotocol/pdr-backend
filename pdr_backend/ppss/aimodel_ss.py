from typing import Optional

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import MultiFeedMixin
from pdr_backend.util.strutil import StrMixin

APPROACH_OPTIONS = ["LinearLogistic", "LinearSVC", "Constant"]
WEIGHT_RECENT_OPTIONS = ["10x_5x", "None"]
BALANCE_CLASSES_OPTIONS = ["SMOTE", "RandomOverSampler", "None"]
CALIBRATE_PROBS_OPTIONS = ["CalibratedClassifierCV_5x", "None"]


@enforce_types
class AimodelSS(MultiFeedMixin, StrMixin):
    __STR_OBJDIR__ = ["d"]
    FEEDS_KEY = "input_feeds"

    def __init__(self, d: dict):
        super().__init__(
            d, assert_feed_attributes=["signal"]
        )  # yaml_dict["aimodel_ss"]

        # test inputs
        if not 0 < self.max_n_train:
            raise ValueError(self.max_n_train)
        if not 0 < self.autoregressive_n < np.inf:
            raise ValueError(self.autoregressive_n)

        if self.approach not in APPROACH_OPTIONS:
            raise ValueError(self.approach)
        if self.weight_recent not in WEIGHT_RECENT_OPTIONS:
            raise ValueError(self.weight_recent)
        if self.balance_classes not in BALANCE_CLASSES_OPTIONS:
            raise ValueError(self.balance_classes)
        if self.calibrate_probs not in CALIBRATE_PROBS_OPTIONS:
            raise ValueError(self.calibrate_probs)

    # --------------------------------
    # yaml properties

    @property
    def max_n_train(self) -> int:
        """eg 50000. It's subject to what data is actually available"""
        return self.d["max_n_train"]

    @property
    def autoregressive_n(self) -> int:
        """eg 10. model inputs ar_n past pts z[t-1], .., z[t-ar_n]"""
        return self.d["autoregressive_n"]

    @property
    def approach(self) -> str:
        """eg 'LinearLogistic'"""
        return self.d["approach"]

    @property
    def weight_recent(self) -> str:
        """eg '10x_5x'"""
        return self.d["weight_recent"]

    @property
    def balance_classes(self) -> str:
        """eg 'SMOTE'"""
        return self.d["balance_classes"]

    @property
    def calibrate_probs(self) -> str:
        """eg 'CalibratedClassifierCV_5x'"""
        return self.d["calibrate_probs"]

    # input feeds defined in base

    # --------------------------------
    # derivative properties
    @property
    def n(self) -> int:
        """Number of input dimensions == # columns in X"""
        return self.n_feeds * self.autoregressive_n


# =========================================================================
# utilities for testing


@enforce_types
def aimodel_ss_test_dict(
    input_feeds: Optional[list] = None,
    max_n_train: Optional[int] = None,
    autoregressive_n: Optional[int] = None,
    approach: Optional[str] = None,
    weight_recent: Optional[str] = None,
    balance_classes: Optional[str] = None,
    calibrate_probs: Optional[str] = None,
) -> dict:
    """Use this function's return dict 'd' to construct AimodelSS(d)"""
    d = {
        "input_feeds": input_feeds or ["binance BTC/USDT c"],
        "max_n_train": 7 if max_n_train is None else max_n_train,
        "autoregressive_n": 3 if autoregressive_n is None else autoregressive_n,
        "approach": approach or "LinearLogistic",
        "weight_recent": weight_recent or "10x_5x",
        "balance_classes": balance_classes or "SMOTE",
        "calibrate_probs": calibrate_probs or "CalibratedClassifierCV_5x",
    }
    return d
