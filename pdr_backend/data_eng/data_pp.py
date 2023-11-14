from enforce_typing import enforce_types
import numpy as np

from pdr_backend.util.constants import (
    CAND_USDCOINS,
    CAND_TIMEFRAMES,
    CAND_SIGNALS,
)
from pdr_backend.util.feedstr import (
    unpack_pair_str,
    unpack_feed_str,
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
        timeframe: str,  # eg "1m", "1h"
        predict_feed_str: str,  # eg "binance c BTC/USDT", "kraken h BTC/USDT"
        N_test: int,  # eg 100. num pts to test on, 1 at a time (online)
    ):
        # test inputs
        assert timeframe in CAND_TIMEFRAMES

        _, signal, pair_str = unpack_feed_str(predict_feed_str)
        assert signal in CAND_SIGNALS, signal
        _, quote_str = unpack_pair_str(pair_str)
        assert quote_str in CAND_USDCOINS

        assert 0 < N_test < np.inf

        # save values
        self.timeframe = timeframe
        self.predict_feed_str = predict_feed_str
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

    @property
    def yval_exchange_id(self) -> str:
        """Return e.g. 'binance'"""
        exchange_id, _, _ = unpack_feed_str(self.predict_feed_str)
        return exchange_id

    @property
    def yval_signal(self) -> str:
        """Return e.g. 'high'"""
        _, signal, _ = unpack_feed_str(self.predict_feed_str)
        assert signal in CAND_SIGNALS
        return signal

    @property
    def yval_coin(self) -> str:
        """Return e.g. 'ETH'"""
        _, _, pair_str = unpack_feed_str(self.predict_feed_str)
        base_str, _ = unpack_pair_str(pair_str)
        return base_str

    @property
    def usdcoin(self) -> str:
        """Return e.g. 'USDT'"""
        _, _, pair_str = unpack_feed_str(self.predict_feed_str)
        _, quote_str = unpack_pair_str(pair_str)
        return quote_str

    @enforce_types
    def __str__(self) -> str:
        s = "DataPP={\n"

        s += f"  timeframe={self.timeframe}\n"
        s += f"  predict_feed_str={self.predict_feed_str}\n"
        s += f"  N_test={self.N_test} -- # pts to test on, 1 at a time\n"

        s += "/DataPP}\n"
        return s
