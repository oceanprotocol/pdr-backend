import copy
import logging
import os

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import MultiFeedMixin
from pdr_backend.util.timeutil import pretty_timestr, timestr_to_ut

logger = logging.getLogger("lake_ss")


class LakeSS(MultiFeedMixin):
    FEEDS_KEY = "feeds"

    @enforce_types
    def __init__(self, d: dict):
        # yaml_dict["lake_ss"]
        super().__init__(d, assert_feed_attributes=["timeframe"])

        # handle parquet_dir
        assert self.parquet_dir == os.path.abspath(self.parquet_dir)
        if not os.path.exists(self.parquet_dir):
            logger.warning(
                "Could not find parquet dir, creating one at: %s", self.parquet_dir
            )
            os.makedirs(self.parquet_dir)

        # test inputs
        assert (
            0
            <= timestr_to_ut(self.st_timestr)
            <= timestr_to_ut(self.fin_timestr)
            <= np.inf
        )

    # --------------------------------
    # yaml properties
    @property
    def parquet_dir(self) -> str:
        s = self.d["parquet_dir"]
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

    # feeds defined in base

    # --------------------------------
    # derivative properties
    @property
    def st_timestamp(self) -> int:
        """
        Return start timestamp, in ut: unix time, in ms, in UTC time zone
        Calculated from self.st_timestr.
        """
        return timestr_to_ut(self.st_timestr)

    @property
    def fin_timestamp(self) -> int:
        """
        Return fin timestamp, in ut: unix time, in ms, in UTC time zone
        Calculated from self.fin_timestr.

        ** This value will change dynamically if fin_timestr is "now".
        """
        return timestr_to_ut(self.fin_timestr)

    @enforce_types
    def __str__(self) -> str:
        s = "LakeSS:\n"
        s += f"feeds_strs={self.feeds_strs}"
        s += f" -> n_inputfeeds={self.n_feeds}\n"
        s += f"st_timestr={self.st_timestr}"
        s += f" -> st_timestamp={pretty_timestr(self.st_timestamp)}\n"
        s += f"fin_timestr={self.fin_timestr}"
        s += f" -> fin_timestamp={pretty_timestr(self.fin_timestamp)}\n"
        s += f" -> n_exchs={self.n_exchs}\n"
        s += f"parquet_dir={self.parquet_dir}\n"
        s += "-" * 10 + "\n"
        return s

    @enforce_types
    def copy(self):
        d2 = copy.deepcopy(self.d)

        return LakeSS(d2)
