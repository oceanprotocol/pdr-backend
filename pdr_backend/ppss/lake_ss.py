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

        assert isinstance(self.export_db_data_to_parquet_files, bool)
        assert isinstance(self.seconds_between_parquet_exports, int)
        assert isinstance(self.number_of_files_after_which_re_export_db, int)

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

    @property
    def export_db_data_to_parquet_files(self) -> str:
        return self.d["export_db_data_to_parquet_files"]  # eg True, False

    @property
    def seconds_between_parquet_exports(self) -> str:
        return self.d["seconds_between_parquet_exports"]  # eg 3600

    @property
    def number_of_files_after_which_re_export_db(self) -> str:
        return self.d["number_of_files_after_which_re_export_db"]  # eg 100

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
        s += f"export_db_data_to_parquet_files={self.export_db_data_to_parquet_files}\n"
        s += f"seconds_between_parquet_exports={self.seconds_between_parquet_exports}\n"
        s += "number_of_files_after_which_re_export_db"
        s += f"={self.number_of_files_after_which_re_export_db}\n"
        s += "-" * 10 + "\n"
        return s


# =========================================================================
# utilities for testing


@enforce_types
# pylint: disable=too-many-positional-arguments
def lake_ss_test_dict(
    lake_dir: str,
    feeds: Optional[list] = None,
    st_timestr: Optional[str] = None,
    fin_timestr: Optional[str] = None,
    timeframe: Optional[str] = None,
    export_db_data_to_parquet_files: Optional[bool] = None,
    seconds_between_parquet_exports: Optional[bool] = None,
    number_of_files_after_which_re_export_db: Optional[bool] = None,
):
    """Use this function's return dict 'd' to construct LakeSS(d)"""
    d = {
        "feeds": feeds or ["binance BTC/USDT c 5m"],
        "lake_dir": lake_dir,
        "st_timestr": st_timestr or "2023-06-18",
        "fin_timestr": fin_timestr or "2023-06-30",
        "timeframe": timeframe or "5m",
        "export_db_data_to_parquet_files": export_db_data_to_parquet_files or True,
        "seconds_between_parquet_exports": seconds_between_parquet_exports or 3600,
        "number_of_files_after_which_re_export_db": number_of_files_after_which_re_export_db
        or 100,
    }
    return d
