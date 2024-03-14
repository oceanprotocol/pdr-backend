from collections import OrderedDict
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.dictutil import keyval
from pdr_backend.util.point_meta import PointMeta
from pdr_backend.util.strutil import StrMixin

logger = logging.getLogger("multisim_ss")

APPROACH_OPTIONS = ["SimpleSweep"]  # future: "FastSweep" too


class MultisimSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["multisim_ss"]

        if self.approach not in APPROACH_OPTIONS:
            raise ValueError(self.approach)
        
        assert self.point_meta.n_points > 1

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
    def point_meta(self) -> PointMeta:
        """Returns the sweep_params as a PointMeta, so easy to work with."""
        point_meta_d = OrderedDict({})
        for param_d in self.sweep_params: 
            name, vals_str = keyval(param_d)
            vals = [val.strip() for val in vals_str.split(",")]
            point_meta_d[name] = vals
        return PointMeta(point_meta_d)

    @property
    def n_points(self) -> int:
        """Return # combinations = cross product across all parameters"""
        return self.point_meta.n_points

    @enforce_types
    def point_i(self, i: int) -> Dict[str, Any]:
        return self.point_meta.point_i(i)

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
