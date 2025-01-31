import logging
import os
from typing import Optional

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin

logger = logging.getLogger("sim_ss")

TRADETYPE_OPTIONS = ["livemock", "livereal", "histmock"]

TRANSFORM_OPTIONS = ["center_on_recent", "None"]


@enforce_types
class SimSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["sim_ss"]

        # handle log_dir; self.log_dir is supposed to be path-expanded version
        assert self.log_dir == os.path.abspath(self.log_dir)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            s = f"Couldn't find log dir, so created one at: {self.log_dir}"
            logger.warning(s)

        # validate data
        self.validate_tradetype(self.tradetype)
        self.validate_test_n(self.test_n)
        self.validate_transform(self.transform)
        self.validate_xy_dir(self.xy_dir)  # engine creates log dir when needed

    # --------------------------------
    # validators
    @staticmethod
    def validate_tradetype(tradetype: str):
        if not isinstance(tradetype, str):
            raise TypeError(tradetype)
        if tradetype not in TRADETYPE_OPTIONS:
            raise ValueError(tradetype)

    @staticmethod
    def validate_test_n(test_n: int):
        if not isinstance(test_n, int):
            raise TypeError(test_n)
        if not 0 < test_n < np.inf:
            raise ValueError(test_n)

    @staticmethod
    def validate_transform(transform: str):
        if not isinstance(transform, str):
            raise TypeError(transform)
        if transform not in TRANSFORM_OPTIONS:
            raise ValueError(transform)

    @staticmethod
    def validate_xy_dir(xy_dir: str):
        if not isinstance(xy_dir, str):
            raise TypeError(xy_dir)

    # --------------------------------
    # properties direct from yaml dict
    @property
    def log_dir(self) -> str:
        s = self.d["log_dir"]
        if s != os.path.abspath(s):  # rel path given; needs an abs path
            return os.path.abspath(s)
        # abs path given
        return s

    @property
    def tradetype(self) -> str:
        return self.d.get("tradetype", "histmock")

    @property
    def test_n(self) -> int:
        return self.d["test_n"]  # eg 200

    @property
    def transform(self) -> str:
        return self.d["transform"]

    @property
    def xy_dir(self) -> str:
        return self.d["xy_dir"]  # engine expands path when needed; not here

    # --------------------------------
    # derived methods
    def is_final_iter(self, iter_i: int) -> bool:
        """Is 'iter_i' the final iteration?"""
        if iter_i < 0 or iter_i >= self.test_n:
            raise ValueError(iter_i)
        return (iter_i + 1) == self.test_n

    # --------------------------------
    # setters
    def set_tradetype(self, tradetype: str):
        self.validate_tradetype(tradetype)
        self.d["tradetype"] = tradetype

    def set_test_n(self, test_n: int):
        self.validate_test_n(test_n)
        self.d["test_n"] = test_n


# =========================================================================
# utilities for testing


@enforce_types
def sim_ss_test_dict(
    log_dir: str,
    tradetype: Optional[str] = None,
    test_n: Optional[int] = None,
    transform: Optional[str] = None,
    xy_dir: Optional[str] = None,
) -> dict:
    d = {
        "log_dir": log_dir,
        "tradetype": tradetype or "histmock",
        "test_n": test_n or 10,
        "transform": transform or "None",
        "xy_dir": xy_dir or "None",
    }
    return d
