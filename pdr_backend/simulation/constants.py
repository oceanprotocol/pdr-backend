import numpy as np

OHLCV_COLS = ["open", "high", "low", "close", "volume"]
OHLCV_DTYPES = [np.float64] * len(OHLCV_COLS)

TOHLCV_COLS = ["timestamp"] + OHLCV_COLS
TOHLCV_DTYPES = [np.int64] + OHLCV_DTYPES

# 1 min = 60000 ms, 5 min = 300000 ms, 6 min = 360000 ms, 12 min = 720000 ms
MS_PER_EPOCH = 300000
MS_PER_EPOCH_MN = 200000 # lower bound before warning
MS_PER_EPOCH_MX = 720000 # upper bound before warning
