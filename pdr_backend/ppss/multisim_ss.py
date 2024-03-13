import logging
from typing import List, Optional

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin

logger = logging.getLogger("multisim_ss")

APPROACH_OPTIONS = ["SimpleSweep"] # future: "FastSweep" too

@enforce_types
class MultisimSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["multisim_ss"]
        
        if self.approach not in APPROACH_OPTIONS:
            raise ValueError(self.approach)

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
        for param_d in self.sweep_params:
            # eg d = {'trader_ss.buy_amt': '10 USD, 20 USD'}
            vals_str = _val(param_d) # eg '10 USD, '20 USD'
            vals = vals_str.split(",") # eg ['10 USD', '20 USD']
            n_combos *= len(vals)
        return n_combos

@enforce_types
def _val(d: dict) -> tuple:
    """d has just one item, e.g. {'thekey': 'theval'}. Return the val"""
    (_, val) =  _keyval(d)
    return val

@enforce_types
def _keyval(d: dict) -> tuple:
    """d has just one item, e.g. {'thekey': 'theval'}. We return key & val"""
    assert len(d) == 1, (len(d), d)
    (key, val) = [i for i in d.items()][0]
    return (key, val)
    
# =========================================================================
# utilities for testing


@enforce_types
def multisim_ss_test_dict(
        approach: Optional[str] = None,
        sweep_params: Optional[list] = None,
        ) -> dict:
    approach = approach or "SimpleSweep"
    sweep_params = sweep_params or \
        [{'predictoor_ss.aimodel_ss.autoregressive_n': '1, 2'}]
    d = {
        "approach": approach,
        "sweep_params": sweep_params,
    }
    return d
