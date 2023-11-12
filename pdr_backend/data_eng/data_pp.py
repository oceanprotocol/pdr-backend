from enforce_typing import enforce_types
import numpy as np

from pdr_backend.data_eng.constants import (
    CAND_USDCOINS,
    CAND_TIMEFRAMES,
    CAND_SIGNALS,
)


class DataPP:  # user-uncontrollable params, at data-eng level
    """
    DataPP specifies the output variable (yval), ie what to predict.

    DataPP is problem definition -> uncontrollable.
    DataSS is solution strategy -> controllable.
    For a given problem definition (DataPP), you can try different DataSS vals
    """

    # pylint: disable=too-many-instance-attributes
    @enforce_types
    def __init__(
        self,
        timeframe: str,  # "1m", 5m, 15m, 30m, 1h, 1d, 1w, 1M
        yval_exchange_id: str,  # eg "binance",
        yval_coin: str,  # eg "ETH"
        usdcoin: str,  # e.g. "USDT", for pairs of eg ETH-USDT, BTC-USDT
        yval_signal: str,  # eg "c" for closing price
        N_test: int,  # eg 100. num pts to test on, 1 at a time (online)
    ):
        assert 0 < N_test < np.inf

        assert usdcoin in CAND_USDCOINS
        assert timeframe in CAND_TIMEFRAMES
        assert yval_signal in CAND_SIGNALS, yval_signal

        self.timeframe = timeframe
        self.usdcoin = usdcoin
        self.yval_exchange_id = yval_exchange_id
        self.yval_coin = yval_coin
        self.yval_signal = yval_signal
        self.N_test = N_test

    @property
    def timeframe_ms(self) -> int:
        """Returns timeframe, in ms"""
        return self.timeframe_m * 60 * 1000

    @property
    def timeframe_m(self) -> int:
        """Returns timeframe, in minutes"""
        if self.timeframe == "5m":
            return 5
        if self.timeframe == "1h":
            return 60
        raise ValueError("need to support timeframe={self.timeframe}")

    @enforce_types
    def __str__(self) -> str:
        s = "DataPP={\n"

        s += f"  timeframe={self.timeframe}\n"
        s += f"  yval_exchange_id={self.yval_exchange_id}\n"
        s += f"  yval_coin={self.yval_coin}\n"
        s += f"  usdcoin={self.usdcoin}\n"
        s += f"  yval_signal={self.yval_signal}\n"
        s += f"  N_test={self.N_test} -- # pts to test on, 1 at a time\n"

        s += "/DataPP}\n"
        return s
