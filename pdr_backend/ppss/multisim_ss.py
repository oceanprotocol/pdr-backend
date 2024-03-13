import logging
from typing import List

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin

logger = logging.getLogger("multisim_ss")


@enforce_types
class MultisimSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["multisim_ss"]

    # --------------------------------
    # properties direct from yaml dict
    @property
    def approach(self) -> str:
        """Return e.g. 'simplesweep'"""
        return self.d["approach"]

    @property
    def sweep_params(self) -> list:
        return self.d["sweep_params"]
    
    # --------------------------------
    # derivative properties
    @property
    def n_combos(self) -> int:
        """Return # combinations = cross product across all parameters"""
        n_combos = 1
        for param in self.sweep_params: # eg trader_ss.buy_amt
            n_values_for_param = FIXME(param)
            n_runs *= n_values_for_param
        return n_runs
    


@enforce_types
def multisim_ss_test_dict(sweep_params: list) -> dict:
    d = {
        "approach": "simplesweep",
        "sweep_params": sweep_params,
    }
    return d
