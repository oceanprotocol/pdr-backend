from enforce_typing import enforce_types

from pdr_backend.util.constants import (
    CAND_TIMEFRAMES,
    CAND_USDCOINS,
    CHAR_TO_SIGNAL,
    S_PER_DAY,
    S_PER_MIN,
)


@enforce_types
def test_util_constants():
    assert S_PER_MIN == 60
    assert S_PER_DAY == 86400

    assert "USDT" in CAND_USDCOINS
    assert "5m" in CAND_TIMEFRAMES
    assert "close" in CHAR_TO_SIGNAL.values()
    assert len(CHAR_TO_SIGNAL) == 5
    assert CHAR_TO_SIGNAL["c"] == "close"
