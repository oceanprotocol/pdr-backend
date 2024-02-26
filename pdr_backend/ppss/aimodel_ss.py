import copy

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import MultiFeedMixin
from pdr_backend.util.strutil import StrMixin

APPROACHES = ["LinearLogistic", "LinearSVC"]


@enforce_types
class AimodelSS(MultiFeedMixin, StrMixin):
    __STR_OBJDIR__ = ["d"]
    FEEDS_KEY = "input_feeds"

    def __init__(self, d: dict):
        super().__init__(
            d, assert_feed_attributes=["signal"]
        )  # yaml_dict["aimodel_ss"]

        # test inputs
        if self.approach not in APPROACHES:
            raise ValueError(self.approach)

        assert 0 < self.max_n_train
        assert 0 < self.autoregressive_n < np.inf

    # --------------------------------
    # yaml properties

    @property
    def approach(self) -> str:
        return self.d["approach"]  # eg "LinearLogistic"

    @property
    def max_n_train(self) -> int:
        return self.d["max_n_train"]  # eg 50000. S.t. what data is available

    @property
    def autoregressive_n(self) -> int:
        return self.d[
            "autoregressive_n"
        ]  # eg 10. model inputs ar_n past pts z[t-1], .., z[t-ar_n]

    # input feeds defined in base

    # --------------------------------
    # derivative properties
    @property
    def n(self) -> int:
        """Number of input dimensions == # columns in X"""
        return self.n_feeds * self.autoregressive_n
