import os
from typing import List

import ccxt
from enforce_typing import enforce_types
import numpy as np

from pdr_backend.data_eng.constants import CAND_SIGNALS
from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.util.timeutil import pretty_timestr


class DataSS:  # user-controllable params, at data-eng level
    """
    DataPP specifies the output variable (yval), ie what to predict.

    DataPP is problem definition -> uncontrollable.
    DataSS is solution strategy -> controllable.
    For a given problem definition (DataPP), you can try different DataSS vals

    DataSS specifies the inputs, and how much training data to get
      - Input vars: Nt vars for each of {all signals}x{all coins}x{all exch}
      - How much trn data: time range st->fin_timestamp, bound by max_N_trn
    """

    # pylint: disable=too-many-instance-attributes
    @enforce_types
    def __init__(
        self,
        csv_dir: str,  # eg "csvs". abs or rel loc'n of csvs dir
        st_timestamp: int,  # ut, eg timestr_to_ut("2019-09-13_04:00")
        fin_timestamp: int,  # ut, eg timestr_to_ut("now")
        max_N_train,  # eg 50000. if inf, only limited by data available
        Nt: int,  # eg 10. # model inputs Nt past pts z[t-1], .., z[t-Nt]
        signals: List[str],  # for model input vars. eg ["open","high","volume"]
        coins: List[str],  # for model input vars. eg ["ETH", "BTC"]
        exchange_ids: List[str],  # for model input vars.eg ["binance","kraken"]
    ):
        if not os.path.exists(csv_dir):
            print(f"Could not find csv dir, creating one at: {csv_dir}")
            os.makedirs(csv_dir)
        assert 0 <= st_timestamp <= fin_timestamp <= np.inf
        assert 0 < max_N_train
        assert 0 < Nt < np.inf
        unknown_signals = set(signals) - set(CAND_SIGNALS)
        assert not unknown_signals, unknown_signals

        self.csv_dir = csv_dir
        self.st_timestamp = st_timestamp
        self.fin_timestamp = fin_timestamp

        self.max_N_train = max_N_train
        self.Nt = Nt

        self.signals = signals
        self.coins = coins

        self.exchs_dict = {}  # e.g. {"binance" : ccxt.binance()}
        for exchange_id in exchange_ids:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchs_dict[exchange_id] = exchange_class()

    @property
    def n(self) -> int:
        """Number of input dimensions == # columns in X"""
        return self.n_exchs * self.n_coins * self.n_signals * self.Nt

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
        s += f"  st_timestamp={pretty_timestr(self.st_timestamp)}\n"
        s += f"  fin_timestamp={pretty_timestr(self.fin_timestamp)}\n"
        s += "  \n"

        s += f"  max_N_train={self.max_N_train} -- max # pts to train on\n"
        s += f"  Nt={self.Nt} -- model inputs Nt past pts z[t-1], .., z[t-Nt]\n"
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
            st_timestamp=self.st_timestamp,
            fin_timestamp=self.fin_timestamp,
            max_N_train=self.max_N_train,
            Nt=self.Nt,
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
