
import ccxt
from enforce_typing import enforce_types
import pytest

from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv_ccxt
from pdr_backend.util.time_types import UnixTimeMs

@enforce_types
def test_safe_fetch_ohlcv_ccxt_binance():
    exch = ccxt.binanceus()
    _test_safe_fetch_ohlcv_ccxt(exch)

    
@enforce_types
def test_safe_fetch_ohlcv_ccxt_kraken():
    exch = ccxt.kraken()
    _test_safe_fetch_ohlcv_ccxt(exch)    

    
@enforce_types
def _test_safe_fetch_ohlcv_ccxt(exch):
    since = UnixTimeMs.from_timestr("2023-06-18")
    symbol, timeframe, limit = "ETH/USDT", "5m", 1000

    # happy path ccxt
    raw_tohlc_data = safe_fetch_ohlcv_ccxt(exch, symbol, timeframe, since, limit)
    assert_raw_tohlc_data_ok(raw_tohlc_data)

    # catch bad (but almost good) symbol
    with pytest.raises(ValueError):
        raw_tohlc_data = safe_fetch_ohlcv_ccxt(
            exch, "ETH-USDT", timeframe, since, limit
        )

    # it will catch type errors, except for exch. Test an example of this.
    with pytest.raises(TypeError):
        raw_tohlc_data = safe_fetch_ohlcv_ccxt(exch, 11, timeframe, since, limit)
    with pytest.raises(TypeError):
        raw_tohlc_data = safe_fetch_ohlcv_ccxt(exch, symbol, 11, since, limit)
    with pytest.raises(TypeError):
        raw_tohlc_data = safe_fetch_ohlcv_ccxt(exch, symbol, timeframe, "f", limit)
    with pytest.raises(TypeError):
        raw_tohlc_data = safe_fetch_ohlcv_ccxt(exch, symbol, timeframe, since, "f")

    # should not crash, just give warning
    safe_fetch_ohlcv_ccxt("bad exch", symbol, timeframe, since, limit)
    safe_fetch_ohlcv_ccxt(exch, "bad symbol", timeframe, since, limit)
    safe_fetch_ohlcv_ccxt(exch, symbol, "bad timeframe", since, limit)

    # ensure a None is returned when warning
    v = safe_fetch_ohlcv_ccxt("bad exch", symbol, timeframe, since, limit)
    assert v is None



@enforce_types
def assert_raw_tohlc_data_ok(raw_tohlc_data):
    assert raw_tohlc_data, raw_tohlc_data
    assert isinstance(raw_tohlc_data, list)
    for item in raw_tohlc_data:
        assert len(item) == (6)
        assert isinstance(item[0], int)
        for val in item[1:]:
            assert isinstance(val, float)
