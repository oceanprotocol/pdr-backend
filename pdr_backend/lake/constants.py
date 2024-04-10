import numpy as np
import polars as pl

OHLCV_COLS = ["open", "high", "low", "close", "volume"]
OHLCV_DTYPES = [np.float64] * len(OHLCV_COLS)

BASE_URL_DYDX = "https://indexer.dydx.trade/v4"

# all possible resolution values are listed at:
# https://docs.dydx.exchange/developers/indexer/indexer_api#enumerated-values
TIMEFRAME_TO_DYDX_RESOLUTION = {"5m": "5MINS", "1h": "1HOUR"}

TOHLCV_COLS = ["timestamp"] + OHLCV_COLS
TOHLCV_DTYPES = [np.int64] + OHLCV_DTYPES

OHLCV_DTYPES_PL = [pl.Float64] * len(OHLCV_COLS)
TOHLCV_DTYPES_PL = [pl.Int64] + OHLCV_DTYPES_PL

TOHLCV_SCHEMA_PL = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))

# warn if OHLCV_MULT_MIN * timeframe < time-between-data < OHLCV_MULT_MAX * t
OHLCV_MULT_MIN = 0.5
OHLCV_MULT_MAX = 2.5

DEFAULT_YAML_FILE = "ppss.yaml"
