import copy
import os
from typing import List, Set, Tuple

import ccxt
import numpy as np
from enforce_typing import enforce_types

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.util.feedstr import Feeds, verify_feeds_strs
from pdr_backend.util.timeutil import pretty_timestr, timestr_to_ut


class DataSS:
    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["data_ss"]

        # handle parquet_dir
        assert self.parquet_dir == os.path.abspath(self.parquet_dir)
        if not os.path.exists(self.parquet_dir):
            print(f"Could not find parquet dir, creating one at: {self.parquet_dir}")
            os.makedirs(self.parquet_dir)

        # test inputs
        assert (
            0
            <= timestr_to_ut(self.st_timestr)
            <= timestr_to_ut(self.fin_timestr)
            <= np.inf
        )
        assert 0 < self.max_n_train
        assert 0 < self.autoregressive_n < np.inf
        verify_feeds_strs(self.input_feeds_strs)

        # save self.exchs_dict
        self.exchs_dict: dict = {}  # e.g. {"binance" : ccxt.binance()}
        feeds = Feeds.from_strs(self.input_feeds_strs)
        for feed in feeds:
            exchange_class = getattr(ccxt, feed.exchange)
            self.exchs_dict[feed.exchange] = exchange_class()

    # --------------------------------
    # yaml properties
    @property
    def input_feeds_strs(self) -> List[str]:
        return self.d["input_feeds"]  # eg ["binance ohlcv BTC/USDT",..]

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

    @property
    def max_n_train(self) -> int:
        return self.d["max_n_train"]  # eg 50000. S.t. what data is available

    @property
    def autoregressive_n(self) -> int:
        return self.d[
            "autoregressive_n"
        ]  # eg 10. model inputs ar_n past pts z[t-1], .., z[t-ar_n]

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

    @property
    def n(self) -> int:
        """Number of input dimensions == # columns in X"""
        return self.n_input_feeds * self.autoregressive_n

    @property
    def n_exchs(self) -> int:
        return len(self.exchs_dict)

    @property
    def exchange_strs(self) -> List[str]:
        return sorted(self.exchs_dict.keys())

    @property
    def n_input_feeds(self) -> int:
        return len(self.input_feeds)

    @property
    def input_feeds(self) -> Feeds:
        """Return list of Feed(exchange_str, signal_str, pair_str)"""
        return Feeds.from_strs(self.input_feeds_strs)

    @property
    def exchange_pair_tups(self) -> Set[Tuple[str, str]]:
        """Return set of unique (exchange_str, pair_str) tuples"""
        return set((feed.exchange, feed.pair) for feed in self.input_feeds)

    @enforce_types
    def __str__(self) -> str:
        s = "DataSS:\n"
        s += f"input_feeds_strs={self.input_feeds_strs}"
        s += f" -> n_inputfeeds={self.n_input_feeds}\n"
        s += f"st_timestr={self.st_timestr}"
        s += f" -> st_timestamp={pretty_timestr(self.st_timestamp)}\n"
        s += f"fin_timestr={self.fin_timestr}"
        s += f" -> fin_timestamp={pretty_timestr(self.fin_timestamp)}\n"
        s += f"max_n_train={self.max_n_train}"
        s += f", autoregressive_n=ar_n={self.autoregressive_n}"
        s += f" -> n = n_input_feeds * ar_n = {self.n} = # inputs to model\n"
        s += f"exchs_dict={self.exchs_dict}"
        s += f" -> n_exchs={self.n_exchs}\n"
        s += f"parquet_dir={self.parquet_dir}\n"
        s += "-" * 10 + "\n"
        return s

    @enforce_types
    def copy_with_yval(self, data_pp: DataPP):
        """Copy self, add data_pp's feeds to new data_ss' inputs as needed"""
        d2 = copy.deepcopy(self.d)

        for predict_feed in data_pp.predict_feeds:
            if predict_feed in self.input_feeds:
                continue
            d2["input_feeds"].append(str(predict_feed))

        return DataSS(d2)
