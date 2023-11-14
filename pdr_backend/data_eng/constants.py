import numpy as np

OHLCV_COLS = ["open", "high", "low", "close", "volume"]
OHLCV_DTYPES = [np.float64] * len(OHLCV_COLS)

TOHLCV_COLS = ["timestamp"] + OHLCV_COLS
TOHLCV_DTYPES = [np.int64] + OHLCV_DTYPES

# warn if OHLCV_MULT_MIN * timeframe < time-between-data < OHLCV_MULT_MAX * t
OHLCV_MULT_MIN = 0.5
OHLCV_MULT_MAX = 2.5
