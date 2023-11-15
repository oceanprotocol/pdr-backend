import os
from typing import List, Set, Tuple

import ccxt
from enforce_typing import enforce_types
import numpy as np

from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.util.feedstr import unpack_feeds_strs, verify_feeds_strs
from pdr_backend.util.timeutil import pretty_timestr, timestr_to_ut


class DataSS:  # user-controllable params, at data-eng level
    """
    DataPP specifies the output variable (yval), ie what to predict.

    DataPP is problem definition -> uncontrollable.
    DataSS is solution strategy -> controllable.
    For a given problem definition (DataPP), you can try different DataSS vals

    DataSS specifies the inputs, and how much training data to get
      - Input vars: autoregressive_n vars for each of {all signals}x{all coins}x{all exch}
      - How much trn data: time range st->fin_timestamp, bound by max_N_trn
    """

    # pylint: disable=too-many-instance-attributes
    @enforce_types
    def __init__(
        self,
        input_feeds_strs: List[str],  # eg ["binance ohlcv BTC/USDT", " ", ...]
        csv_dir: str,  # eg "csvs". abs or rel loc'n of csvs dir
        st_timestr: str,  # eg "2019-09-13_04:00" (earliest),  2019-09-13"
        fin_timestr: str,  # eg "now", "2023-09-23_17:55", "2023-09-23"
        max_n_train,  # eg 50000. if inf, only limited by data available
        autoregressive_n: int,  # eg 10. model inputs ar_n past pts z[t-1], .., z[t-ar_n]
    ):
        # preconditions
        if not os.path.exists(csv_dir):
            print(f"Could not find csv dir, creating one at: {csv_dir}")
            os.makedirs(csv_dir)
        assert 0 <= timestr_to_ut(st_timestr) <= timestr_to_ut(fin_timestr) <= np.inf
        assert 0 < max_n_train
        assert 0 < autoregressive_n < np.inf
        verify_feeds_strs(input_feeds_strs)

        # save values
        self.input_feeds_strs: List[str] = input_feeds_strs

        self.csv_dir: str = csv_dir
        self.st_timestr: str = st_timestr
        self.fin_timestr: str = fin_timestr

        self.max_n_train: int = max_n_train
        self.autoregressive_n: int = autoregressive_n

        self.exchs_dict: dict = {}  # e.g. {"binance" : ccxt.binance()}
        feed_tups = unpack_feeds_strs(input_feeds_strs)
        for exchange_str, _, _ in feed_tups:
            exchange_class = getattr(ccxt, exchange_str)
            self.exchs_dict[exchange_str] = exchange_class()

    @property
    def st_timestamp(self) -> int:
        """
        Return start timestamp, in ut.
        Calculated from self.st_timestr.
        """
        return timestr_to_ut(self.st_timestr)

    @property
    def fin_timestamp(self) -> int:
        """
        Return fin timestamp, in ut.
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
        return len(self.input_feed_tups)

    @property
    def input_feed_tups(self) -> List[Tuple[str, str, str]]:
        """Return list of (exchange_str, signal_str, pair_str)"""
        return unpack_feeds_strs(self.input_feeds_strs)

    @property
    def exchange_pair_tups(self) -> Set[Tuple[str, str]]:
        """Return set of unique (exchange_str, pair_str) tuples"""
        return set(
            (exch_str, pair_str) for (exch_str, _, pair_str) in self.input_feed_tups
        )

    @enforce_types
    def __str__(self) -> str:
        s = "DataSS={\n"

        s += f"  input_feeds_strs={self.input_feeds_strs}"
        s += f"  -> n_inputfeeds={self.n_input_feeds}"
        s += "  \n"

        s += f"  csv_dir={self.csv_dir}\n"
        s += f"  st_timestr={self.st_timestr}\n"
        s += f"  -> st_timestamp={pretty_timestr(self.st_timestamp)}\n"
        s += f"  fin_timestr={self.fin_timestr}\n"
        s += f"  -> fin_timestamp={pretty_timestr(self.fin_timestamp)}\n"
        s += "  \n"

        s += f"  max_n_train={self.max_n_train} -- max # pts to train on\n"
        s += "  \n"

        s += f"  autoregressive_n={self.autoregressive_n}"
        s += " -- model inputs ar_n past pts z[t-1], .., z[t-ar_n]\n"
        s += "  \n"

        s += f"  -> n_input_feeds * ar_n = n = {self.n}"
        s += "-- # input variables to model\n"
        s += "  \n"

        s += f"  exchs_dict={self.exchs_dict}\n"
        s += f"  -> n_exchs={self.n_exchs}\n"
        s += f"  -> exchange_strs={self.exchange_strs}\n"
        s += "  \n"

        s += "/DataSS}\n"
        return s

    @enforce_types
    def copy_with_yval(self, data_pp: DataPP):
        """Copy self, add data_pp's yval to new data_ss' inputs as needed"""
        input_feeds_strs = self.input_feeds_strs[:]
        if data_pp.predict_feed_tup not in self.input_feed_tups:
            input_feeds_strs.append(data_pp.predict_feed_str)

        return DataSS(
            input_feeds_strs=input_feeds_strs,
            csv_dir=self.csv_dir,
            st_timestr=self.st_timestr,
            fin_timestr=self.fin_timestr,
            max_n_train=self.max_n_train,
            autoregressive_n=self.autoregressive_n,
        )
