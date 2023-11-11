from enforce_typing import enforce_types
import numpy as np

from pdr_backend.data_eng.constants import (
    OHLCV_COLS,
    OHLCV_DTYPES,
    TOHLCV_COLS,
    TOHLCV_DTYPES,
    OHLCV_MULT_MIN,
    OHLCV_MULT_MAX,
)


@enforce_types
def test_constants():
    assert len(OHLCV_COLS) == len(OHLCV_DTYPES)
    assert len(TOHLCV_COLS) == len(TOHLCV_DTYPES) == len(OHLCV_COLS) + 1

    assert "high" in OHLCV_COLS
    assert "timestamp" not in OHLCV_COLS
    assert np.float64 in OHLCV_DTYPES
    assert np.int64 not in OHLCV_DTYPES

    assert "high" in TOHLCV_COLS
    assert "timestamp" in TOHLCV_COLS
    assert np.float64 in TOHLCV_DTYPES
    assert np.int64 in TOHLCV_DTYPES

    assert 0 < OHLCV_MULT_MIN <= OHLCV_MULT_MAX < np.inf
