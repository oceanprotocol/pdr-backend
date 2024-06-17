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
        if not 0 < self.max_n_train:
            raise ValueError(self.max_n_train)
        if not 0 < self.autoregressive_n < np.inf:
            raise ValueError(self.autoregressive_n)
        if self.num_diffs == 0:
            raise ValueError(str(self.d))

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

    @property
    def do_diff0(self) -> bool:
        return self.d["do_diff0"]

    @property
    def do_diff1(self) -> bool:
        return self.d["do_diff1"]

    @property
    def do_diff2(self) -> bool:
        return self.d["do_diff2"]

    # ------derived
    @property
    def num_diffs(self) -> bool:
        return int(self.do_diff0 + self.do_diff1 + self.do_diff2)
    
    @property
    def max_diff(self) -> int:
        if self.do_diff2:
            return 2
        if self.do_diff1:
            return 1
        return 0

# =========================================================================
# utilities for testing


@enforce_types
def aimodel_data_ss_test_dict(
    max_n_train: Optional[int] = None,
    autoregressive_n: Optional[int] = None,
    do_diff0: Optional[bool] = True,
    do_diff1: Optional[bool] = False,
    do_diff2: Optional[bool] = False,
) -> dict:
    """Use this function's return dict 'd' to construct AimodelDataSS(d)"""
    d = {
        "max_n_train": 7 if max_n_train is None else max_n_train,
        "autoregressive_n": 3 if autoregressive_n is None else autoregressive_n,
        "do_diff0": do_diff0,
        "do_diff1": do_diff1,
        "do_diff2": do_diff2,
    }
    return d
