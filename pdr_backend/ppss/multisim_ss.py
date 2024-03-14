from collections import OrderedDict
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.point_meta import PointMeta
from pdr_backend.util.strutil import StrMixin

logger = logging.getLogger("multisim_ss")

APPROACH_OPTIONS = ["SimpleSweep"]  # future: "FastSweep" too


@enforce_types
class MultisimSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["multisim_ss"]

        point_meta_d = OrderedDict({})
        for param_d in self.sweep_params: 
            name, vals_str = _keyval(param_d)
            vals = vals_str.split(",") 
            point_meta_d[name] = vals
        self.point_meta = PointMeta(point_meta_d)

        if self.approach not in APPROACH_OPTIONS:
            raise ValueError(self.approach)
        
        assert self.point_meta.n_points() > 1

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
    @enforce_types
    def n_points(self) -> int:
        """Return # combinations = cross product across all parameters"""
        return self.point_meta.n_points()

    @enforce_types
    def point_i(self, i: int) -> Dict[str, Any]:
        return self.point_meta.point_i(i)
    

@enforce_types
def _key(d: dict) -> tuple:
    """d has just one item, e.g. {'thekey': 'theval'}. Return the key"""
    (key, _) = _keyval(d)
    return key

@enforce_types
def _val(d: dict) -> tuple:
    """d has just one item, e.g. {'thekey': 'theval'}. Return the val"""
    (_, val) = _keyval(d)
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
    sweep_params = sweep_params or [
        {"predictoor_ss.aimodel_ss.autoregressive_n": "1, 2"}
    ]
    d = {
        "approach": approach,
        "sweep_params": sweep_params,
    }
    return d
