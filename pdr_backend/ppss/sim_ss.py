import logging
import os
from typing import Optional

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.ccxtutil import CCXTExchangeMixin
from pdr_backend.util.strutil import StrMixin

logger = logging.getLogger("sim_ss")

TRADETYPE_OPTIONS = ["livemock", "livereal", "histmock"]


@enforce_types
class SimSS(StrMixin, CCXTExchangeMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["sim_ss"]

        # check do_plot
        if not isinstance(d["do_plot"], bool):
            raise TypeError

        # handle log_dir; self.log_dir is supposed to be path-expanded version
        assert self.log_dir == os.path.abspath(self.log_dir)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            s = f"Couldn't find log dir, so created one at: {self.log_dir}"
            logger.warning(s)

        # check final_img_filebase
        if not isinstance(d["final_img_filebase"], str):
            raise TypeError

        # check test_n
        test_n = d["test_n"]
        if not isinstance(test_n, int):
            raise TypeError(test_n)
        if not 0 < test_n < np.inf:
            raise ValueError(test_n)

        # check tradetype
        tradetype = d["tradetype"]
        if not isinstance(tradetype, str):
            raise TypeError(tradetype)
        if tradetype not in TRADETYPE_OPTIONS:
            raise ValueError(tradetype)

    # --------------------------------
    # properties direct from yaml dict
    @property
    def do_plot(self) -> bool:
        return self.d["do_plot"]

    @property
    def log_dir(self) -> str:
        s = self.d["log_dir"]
        if s != os.path.abspath(s):  # rel path given; needs an abs path
            return os.path.abspath(s)
        # abs path given
        return s

    @property
    def final_img_filebase(self) -> str:
        return self.d["final_img_filebase"]  # eg "final_img"

    @property
    def test_n(self) -> int:
        return self.d["test_n"]  # eg 200

    @property
    def tradetype(self) -> str:
        return self.d.get("tradetype", "histmock")

    # --------------------------------
    # derived methods
    def is_final_iter(self, iter_i: int) -> bool:
        """Is 'iter_i' the final iteration?"""
        if iter_i < 0 or iter_i >= self.test_n:
            raise ValueError(iter_i)
        return (iter_i + 1) == self.test_n

    def unique_final_img_filename(self) -> str:
        log_dir = self.log_dir
        for try_i in range(1000):
            cand_name = os.path.join(
                log_dir,
                f"{self.final_img_filebase}_{try_i}.png",
            )
            if not os.path.exists(cand_name):
                return cand_name
        raise ValueError("Could not find a unique filename after 1000 tries.")


# =========================================================================
# utilities for testing


@enforce_types
def sim_ss_test_dict(
    do_plot: bool,
    log_dir: str,
    final_img_filebase: Optional[str] = None,
    test_n: Optional[int] = None,
    tradetype: Optional[str] = None,
) -> dict:
    d = {
        "do_plot": do_plot,
        "log_dir": log_dir,
        "final_img_filebase": final_img_filebase or "final_img",
        "test_n": test_n or 10,
        "tradetype": tradetype or "histmock",
        "exchange_only": {
            "timeout": 30000,
            "options": {
                "createMarketBuyOrderRequiresPrice": False,
                "defaultType": "spot",
            },
        },
    }
    return d
