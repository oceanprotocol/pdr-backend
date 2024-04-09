import ccxt
from enforce_typing import enforce_types
import pytest

from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv
from pdr_backend.util.time_types import UnixTimeMs


FAKE_UT = 12345
SYMBOL = "ETH/USDT"
TIMEFRAME = "5m"
SINCE = UnixTimeMs.from_timestr("2023-06-18")
LIMIT = 500

@enforce_types
def test_safe_fetch_ohlcv_1_dydx():
    with patch("safe_fetch_ohlcv_dydx") as mock:
        tohlcv = [FAKE_UT] + [61000.0] * 5
        mock.return_value = tohlcv * LIMIT
        
        exch = "dydx"
        raw_tohlcv_data = safe_fetch_ohlcv(exch, SYMBOL, TIMEFRAME, SINCE, LIMIT)
        assert len(raw_tohlcv_data) == LIMIT
        assert raw_tohlcv_data[0][0] == FAKE_UT
        assert raw_tohlcv_data[0][1] == 61000.0
        

@enforce_types
def test_safe_fetch_ohlcv_2_ccxt():    
    @enforce_types
    class FakeExchange:
        # pylint: disable=unused-argument
        def fetch_ohlcv(self, since, limit, *args, **kwargs) -> list:
            uts: List[int] = [FAKE_UT] * limit
            return [[ut] + [1.0] * 5 for ut in uts]  # 1.0 for open, high, ..

    with patch("ccxt.binanceus") as mock:
        mock.return_value = FakeExchange()
        exch = ccxt.binanceus()
        raw_tohlcv_data = safe_fetch_ohlcv(exch, SYMBOL, TIMEFRAME, SINCE, LIMIT)
        assert len(raw_tohlcv_data) == LIMIT
        assert raw_tohlcv_data[0][0] == FAKE_UT


@enforce_types
def test_safe_fetch_ohlcv_3_bad_paths():
    #bad path: exch = str, but not "dydx"
    with pytest.raises(ValueError):
        exch = "not_dydx"
        _ = safe_fetch_ohlcv(exch, SYMBOL, TIMEFRAME, SINCE, LIMIT)
                       
    #bad path: exch is not str, but not a ccxt exchange either
    with pytest.raises(Exception):
        exch = 3
        _ = safe_fetch_ohlcv(exch, SYMBOL, TIMEFRAME, SINCE, LIMIT)
    
