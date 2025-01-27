from typing import Optional

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class AimodelDataSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        """d -- yaml_dict["aimodel_data_ss"]"""
        self.d = d

        # test inputs
        self.validate_max_n_train(self.max_n_train)
        self.validate_autoregressive_n(self.autoregressive_n)

    # --------------------------------
    # validators
    @staticmethod
    def validate_max_n_train(max_n_train: int):
        if not 0 < max_n_train:
            raise ValueError(max_n_train)

    @staticmethod
    def validate_autoregressive_n(autoregressive_n: int):
        if not 0 < autoregressive_n < np.inf:
            raise ValueError(autoregressive_n)

    # --------------------------------
    # yaml properties

    @property
    def max_n_train(self) -> int:
        """eg 50000. It's subject to what data is actually available"""
        return self.d["max_n_train"]

    @property
    def autoregressive_n(self) -> int:
        """
        eg 10.
        For diff=0, model inputs are past points z[t-1], z[t-2], .., z[t-ar_n]
        For diff=1, add to model_inputs z[t-1]-z[t-2], ..
        For diff=2, add to model_inputs (z[t-1]-z[t-2]) - (z[t-2]-z[t-3]), ..
        """
        return self.d["autoregressive_n"]

    # --------------------------------
    # setters
    def set_max_n_train(self, max_n_train: int):
        self.validate_max_n_train(max_n_train)
        self.d["max_n_train"] = max_n_train

    def set_autoregressive_n(self, autoregressive_n: int):
        self.validate_autoregressive_n(autoregressive_n)
        self.d["autoregressive_n"] = autoregressive_n


# =========================================================================
# utilities for testing


@enforce_types
def aimodel_data_ss_test_dict(
    max_n_train: Optional[int] = None,
    autoregressive_n: Optional[int] = None,
) -> dict:
    """Use this function's return dict 'd' to construct AimodelDataSS(d)"""
    d = {
        "max_n_train": 7 if max_n_train is None else max_n_train,
        "autoregressive_n": 3 if autoregressive_n is None else autoregressive_n,
    }
    return d
