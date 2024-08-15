#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os
from typing import Optional

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import MultiFeedMixin
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("lake_ss")


class LakeSS(MultiFeedMixin):
    FEEDS_KEY = "feeds"

    @enforce_types
    def __init__(self, d: dict):
        # yaml_dict["lake_ss"]
        super().__init__(d, assert_feed_attributes=["timeframe"])

        # handle lake_dir
        assert self.lake_dir == os.path.abspath(self.lake_dir)
        if not os.path.exists(self.lake_dir):
            logger.warning(
                "Could not find lake dir, creating one at: %s", self.lake_dir
            )
            os.makedirs(self.lake_dir)

        # test inputs
        assert (
            0
            <= UnixTimeMs.from_timestr(self.st_timestr)
            <= UnixTimeMs.from_timestr(self.fin_timestr)
            <= np.inf
        )

    # --------------------------------
    # yaml properties
    @property
    def lake_dir(self) -> str:
        s = self.d["lake_dir"]
        if s != os.path.abspath(s):  # rel path given; needs an abs path
            return os.path.abspath(s)
        # abs path given
        return s

    @property
    def st_timestr(self) -> str:
        return self.d["st_timestr"]  # eg "2019-09-13_04:00" (earliest)

    @property
    def fin_timestr(self) -> str:
        return self.d["fin_timestr"]  # eg "now","2023-09-23_17:55","2023-09-23"

    @property
    def api(self) -> str:
        return self.d.get("api", "ccxt")

    # feeds defined in base

    # --------------------------------
    # derivative properties
    @property
    def st_timestamp(self) -> UnixTimeMs:
        """
        Return start timestamp, in ut: unix time, in ms, in UTC time zone
        Calculated from self.st_timestr.
        """
        return UnixTimeMs.from_timestr(self.st_timestr)

    @property
    def fin_timestamp(self) -> UnixTimeMs:
        """
        Return fin timestamp, in ut: unix time, in ms, in UTC time zone
        Calculated from self.fin_timestr.

        ** This value will change dynamically if fin_timestr is "now".
        """
        return UnixTimeMs.from_timestr(self.fin_timestr)

    @enforce_types
    def __str__(self) -> str:
        s = "LakeSS:\n"
        s += f"feeds_strs={self.feeds_strs}"
        s += f" -> n_inputfeeds={self.n_feeds}\n"
        s += f"st_timestr={self.st_timestr}"
        s += f" -> st_timestamp={self.st_timestamp.pretty_timestr()}\n"
        s += f"fin_timestr={self.fin_timestr}"
        s += f" -> fin_timestamp={self.fin_timestamp.pretty_timestr()}\n"
        s += f" -> n_exchs={self.n_exchs}\n"
        s += f"lake_dir={self.lake_dir}\n"
        s += "-" * 10 + "\n"
        return s


# =========================================================================
# utilities for testing


@enforce_types
def lake_ss_test_dict(
    lake_dir: str,
    feeds: Optional[list] = None,
    st_timestr: Optional[str] = None,
    fin_timestr: Optional[str] = None,
    timeframe: Optional[str] = None,
):
    """Use this function's return dict 'd' to construct LakeSS(d)"""
    d = {
        "feeds": feeds or ["binance BTC/USDT c 5m"],
        "lake_dir": lake_dir,
        "st_timestr": st_timestr or "2023-06-18",
        "fin_timestr": fin_timestr or "2023-06-30",
        "timeframe": timeframe or "5m",
    }
    return d
