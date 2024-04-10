from unittest.mock import patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.exchange.fetch_ohlcv import safe_fetch_ohlcv
from pdr_backend.util.time_types import UnixTimeMs


FAKE_UT = 12345
SYMBOL = "ETH/USDT"
TIMEFRAME = "5m"
SINCE = UnixTimeMs.from_timestr("2023-06-18")
LIMIT = 500


@enforce_types
def test_safe_fetch_ohlcv_1_dydx():
    with patch("pdr_backend.exchange.fetch_ohlcv.safe_fetch_ohlcv_dydx") as mock:
        tohlcv = [FAKE_UT] + [1.0] * 5
        mock.return_value = [tohlcv for _ in range(LIMIT)]
        raw_tohlcv_data = safe_fetch_ohlcv(
            "dydx",
            SYMBOL,
            TIMEFRAME,
            SINCE,
            LIMIT,
        )
        assert len(raw_tohlcv_data) == LIMIT
        assert raw_tohlcv_data[0][0] == FAKE_UT
        assert raw_tohlcv_data[0][1] == 1.0


@enforce_types
def test_safe_fetch_ohlcv_2_ccxt():
    @enforce_types
    class FakeExchange:
        # pylint: disable=unused-argument
        def fetch_ohlcv(self, since, limit, *args, **kwargs) -> list:
            tohlcv = [FAKE_UT] + [1.0] * 5
            return [tohlcv for _ in range(limit)]

    with patch("ccxt.binanceus") as mock:
        mock.return_value = FakeExchange()
        raw_tohlcv_data = safe_fetch_ohlcv(
            "binanceus",
            SYMBOL,
            TIMEFRAME,
            SINCE,
            LIMIT,
        )
        assert len(raw_tohlcv_data) == LIMIT
        assert raw_tohlcv_data[0][0] == FAKE_UT


@enforce_types
def test_safe_fetch_ohlcv_3_bad_paths():
    for bad_str in [None, 3, 3.1]:
        with pytest.raises(TypeError):
            _ = safe_fetch_ohlcv(bad_str, SYMBOL, TIMEFRAME, SINCE, LIMIT)

    for bad_str in ["", "  ", "not_dydx", "   dydx"]:
        with pytest.raises(ValueError):
            _ = safe_fetch_ohlcv(bad_str, SYMBOL, TIMEFRAME, SINCE, LIMIT)
