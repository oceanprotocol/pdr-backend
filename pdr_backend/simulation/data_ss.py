import os
from typing import List

import ccxt
from enforce_typing import enforce_types
import numpy as np

from pdr_backend.simulation.timeutil import pretty_timestr

CAND_USDCOINS = ["USDT", "DAI", "USDC"]  # add more if needed
CAND_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"]
CAND_SIGNALS = ["open", "high", "low", "close", "volume"]


class DataSS:
    # pylint: disable=too-many-instance-attributes
    @enforce_types
    def __init__(
        self,
        csv_dir: str,  # abs or relative location of csvs directory
        st_timestamp: int,  # ut, eg via timestr_to_ut(timestr)
        fin_timestamp: int,  # ""
        max_N_train,  # if inf, only limited by data available
        N_test: int,  # eg 100. num pts to test on, 1 at a time (online)
        Nt: int,  # eg 10. # model inputs Nt past pts z[t-1], .., z[t-Nt]
        usdcoin: str,  # e.g. "USDT", for pairs of eg ETH-USDT, BTC-USDT
        timeframe: str,  # "1m", 5m, 15m, 30m, 1h, 1d, 1w, 1M
        signals: List[str],  # eg ["open","high","low","close","volume"]
        coins: List[str],  # eg ["ETH", "BTC"]
        exchange_ids: List[str],  # eg ["binance", "kraken"]
        yval_exchange_id: str,  # eg "binance",
        yval_coin: str,  # eg "ETH"
        yval_signal: str,  # eg "c" for closing price
    ):
        if not os.path.exists(csv_dir):
            print(f"Could not find csv dir, creating one at: {csv_dir}")
            os.makedirs(csv_dir)
        assert 0 <= st_timestamp <= fin_timestamp <= np.inf
        assert 0 < max_N_train
        assert 0 < N_test < np.inf
        assert 0 < Nt < np.inf
        assert usdcoin in CAND_USDCOINS
        assert timeframe in CAND_TIMEFRAMES
        unknown_signals = set(signals) - set(CAND_SIGNALS)
        assert not unknown_signals, unknown_signals
        assert yval_signal in CAND_SIGNALS, yval_signal

        self.csv_dir = csv_dir
        self.st_timestamp = st_timestamp
        self.fin_timestamp = fin_timestamp

        self.max_N_train = max_N_train
        self.N_test = N_test
        self.Nt = Nt

        self.usdcoin = usdcoin
        self.timeframe = timeframe
        self.signals = signals
        self.coins = coins

        self.exchs_dict = {}  # e.g. {"binance" : ccxt.binance()}
        for exchange_id in exchange_ids:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchs_dict[exchange_id] = exchange_class()

        self.yval_exchange_id = yval_exchange_id
        self.yval_coin = yval_coin
        self.yval_signal = yval_signal

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

    def __str__(self) -> str:
        s = "DataSS={\n"

        s += f"  csv_dir={self.csv_dir}\n"
        s += f"  st_timestamp={pretty_timestr(self.st_timestamp)}\n"
        s += f"  fin_timestamp={pretty_timestr(self.fin_timestamp)}\n"
        s += "  \n"

        s += f"  max_N_train={self.max_N_train} -- max # pts to train on\n"
        s += f"  N_test={self.N_test} -- # pts to test on, 1 at a time\n"
        s += f"  Nt={self.Nt} -- model inputs Nt past pts z[t-1], .., z[t-Nt]\n"
        s += "  \n"

        s += f"  usdcoin={self.usdcoin}\n"
        s += f"  timeframe={self.timeframe}\n"
        s += f"  signals={self.signals}\n"
        s += f"  coins={self.coins}\n"
        s += "  \n"

        s += f"  exchs_dict={self.exchs_dict}\n"
        s += f"  yval_exchange_id={self.yval_exchange_id}\n"
        s += f"  yval_coin={self.yval_coin}\n"
        s += f"  yval_signal={self.yval_signal}\n"
        s += "  \n"

        s += "  (then...)\n"
        s += f"  n_exchs={self.n_exchs}\n"
        s += f"  exchange_ids={self.exchange_ids}\n"
        s += f"  n_signals={self.n_signals}\n"
        s += f"  n_coins={self.n_coins}\n"
        s += f"  n={self.n} -- # input variables to model\n"

        s += "/DataSS}\n"
        return s
