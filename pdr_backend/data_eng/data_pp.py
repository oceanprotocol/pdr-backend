from typing import Tuple

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.util.constants import CAND_TIMEFRAMES
from pdr_backend.util.feedstr import unpack_feed_str, verify_feed_str
from pdr_backend.util.pairstr import unpack_pair_str


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
        # preconditions
        assert timeframe in CAND_TIMEFRAMES
        verify_feed_str(predict_feed_str)
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
    def predict_feed_tup(self) -> Tuple[str, str, str]:
        """
        Return (exchange_str, signal_str, pair_str)
        E.g. ("binance", "close", "BTC/USDT")
        """
        return unpack_feed_str(self.predict_feed_str)

    @property
    def exchange_str(self) -> str:
        """Return e.g. 'binance'"""
        return self.predict_feed_tup[0]

    @property
    def signal_str(self) -> str:
        """Return e.g. 'high'"""
        return self.predict_feed_tup[1]

    @property
    def pair_str(self) -> str:
        """Return e.g. 'ETH/USDT'"""
        return self.predict_feed_tup[2]

    @property
    def base_str(self) -> str:
        """Return e.g. 'ETH'"""
        return unpack_pair_str(self.predict_feed_tup[2])[0]

    @property
    def quote_str(self) -> str:
        """Return e.g. 'USDT'"""
        return unpack_pair_str(self.predict_feed_tup[2])[1]

    @enforce_types
    def __str__(self) -> str:
        s = "DataPP={\n"

        s += f"  timeframe={self.timeframe}\n"
        s += f"  predict_feed_str={self.predict_feed_str}\n"
        s += f"  N_test={self.N_test} -- # pts to test on, 1 at a time\n"

        s += "/DataPP}\n"
        return s
