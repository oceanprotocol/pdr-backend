from typing import Optional, Tuple

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin

PRETRANSFORM_OPTIONS = ["boxcox", "None"]

class AimodelDataSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        """d -- yaml_dict["aimodel_data_ss"]"""
        self.d = d

        # test inputs
        if not 0 < self.max_n_train:
            raise ValueError(self.max_n_train)
        if not 0 < self.autoregressive_n < np.inf:
            raise ValueError(self.autoregressive_n)
        if self.pretransform not in PRETRANSFORM_OPTIONS:
            raise ValueError(self.pretransform)

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
    def pretransform(self) -> int:
        """eg 'boxcox' """
        return self.d["pretransform"]


# =========================================================================
# utilities for testing


@enforce_types
def aimodel_data_ss_test_dict(
    max_n_train: Optional[int] = None,
    autoregressive_n: Optional[int] = None,
    pretransform: Optional[str] = None,
) -> dict:
    """Use this function's return dict 'd' to construct AimodelDataSS(d)"""
    d = {
        "max_n_train": 7 if max_n_train is None else max_n_train,
        "autoregressive_n": 3 if autoregressive_n is None else autoregressive_n,
        "pretransform": pretransform or "None",
    }
    return d
