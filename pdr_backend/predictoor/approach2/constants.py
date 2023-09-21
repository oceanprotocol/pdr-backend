import os

import numpy as np

OHLCV_COLS = ["open", "high", "low", "close", "volume"]
OHLCV_DTYPES = [np.float64] * len(OHLCV_COLS)

TOHLCV_COLS = ["timestamp"] + OHLCV_COLS
TOHLCV_DTYPES = [np.int64] + OHLCV_DTYPES


def get_ms_per_epoch():
    return int(os.getenv("SECONDS_PER_EPOCH", "300")) * 1000
