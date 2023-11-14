import os
from typing import List

import ccxt
from enforce_typing import enforce_types
import numpy as np

from pdr_backend.data_eng.constants import CAND_SIGNALS
from pdr_backend.data_eng.data_pp import DataPP
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
        csv_dir: str,  # eg "csvs". abs or rel loc'n of csvs dir
        st_timestr: str,  # eg "2019-09-13_04:00" (earliest),  2019-09-13"
        fin_timestr: str,  # eg "now", "2023-09-23_17:55", "2023-09-23"
        max_n_train,  # eg 50000. if inf, only limited by data available
        autoregressive_n: int,  # eg 10. model inputs ar_n past pts z[t-1], .., z[t-ar_n]
        signals: List[str],  # for model input vars. eg ["open","high","volume"]
        coins: List[str],  # for model input vars. eg ["ETH", "BTC"]
        exchange_ids: List[str],  # for model input vars.eg ["binance","kraken"]
    ):
        if not os.path.exists(csv_dir):
            print(f"Could not find csv dir, creating one at: {csv_dir}")
            os.makedirs(csv_dir)
        assert 0 <= timestr_to_ut(st_timestr) <= timestr_to_ut(fin_timestr) <= np.inf
        assert 0 < max_n_train
        assert 0 < autoregressive_n < np.inf
        unknown_signals = set(signals) - set(CAND_SIGNALS)
        assert not unknown_signals, unknown_signals

        self.csv_dir = csv_dir
        self.st_timestr = st_timestr
        self.fin_timestr = fin_timestr

        self.max_n_train = max_n_train
        self.autoregressive_n = autoregressive_n

        self.signals = signals
        self.coins = coins

        self.exchs_dict = {}  # e.g. {"binance" : ccxt.binance()}
        for exchange_id in exchange_ids:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchs_dict[exchange_id] = exchange_class()

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
        return self.n_exchs * self.n_coins * self.n_signals * self.autoregressive_n

    @property
    def n_exchs(self) -> int:
        return len(self.exchs_dict)

    @property
    def exchange_ids(self) -> List[str]:
        return sorted(self.exchs_dict.keys())

    @property
    def n_signals(self) -> int:
        return len(self.signals)

    @property
    def n_coins(self) -> int:
        return len(self.coins)

    @enforce_types
    def __str__(self) -> str:
        s = "DataSS={\n"

        s += f"  csv_dir={self.csv_dir}\n"
        s += f"  st_timestr={self.st_timestr}\n"
        s += f"  -> st_timestamp={pretty_timestr(self.st_timestamp)}\n"
        s += f"  fin_timestr={self.fin_timestr}\n"
        s += f"  -> fin_timestamp={pretty_timestr(self.fin_timestamp)}\n"
        s += "  \n"

        s += f"  max_n_train={self.max_n_train} -- max # pts to train on\n"

        s += f"  autoregressive_n={self.autoregressive_n}"
        s += " -- model inputs ar_n past pts z[t-1], .., z[t-ar_n]\n"
        s += "  \n"

        s += f"  signals={self.signals}\n"
        s += f"  coins={self.coins}\n"
        s += "  \n"

        s += f"  exchs_dict={self.exchs_dict}\n"
        s += "  \n"

        s += "  (then...)\n"
        s += f"  n_exchs={self.n_exchs}\n"
        s += f"  exchange_ids={self.exchange_ids}\n"
        s += f"  n_signals={self.n_signals}\n"
        s += f"  n_coins={self.n_coins}\n"
        s += f"  n={self.n} -- # input variables to model\n"

        s += "/DataSS}\n"
        return s

    @enforce_types
    def copy_with_yval(self, data_pp: DataPP):
        """Copy self, add data_pp's yval to new data_ss' inputs as needed"""
        return DataSS(
            csv_dir=self.csv_dir,
            st_timestr=self.st_timestr,
            fin_timestr=self.fin_timestr,
            max_n_train=self.max_n_train,
            autoregressive_n=self.autoregressive_n,
            signals=_list_with(self.signals[:], data_pp.yval_signal),
            coins=_list_with(self.coins[:], data_pp.yval_coin),
            exchange_ids=_list_with(self.exchange_ids[:], data_pp.yval_exchange_id),
        )


@enforce_types
def _list_with(list_: list, item) -> list:
    """If l_ has item, return just list_. Otherwise, return list_ + item."""
    if item in list_:
        return list_
    return list_ + [item]
