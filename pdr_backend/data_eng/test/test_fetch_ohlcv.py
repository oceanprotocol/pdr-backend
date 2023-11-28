import ccxt

from enforce_typing import enforce_types
import pytest

from pdr_backend.data_eng.fetch_ohlcv import safe_fetch_ohlcv


@enforce_types
def test_safe_fetch_ohlcv():
    exch = ccxt.binanceus()
    symbol, timeframe, since, limit = "ETH/USDT", "5m", 1701072780919, 10

    # happy path
    raw_tohlc_data = safe_fetch_ohlcv(exch, symbol, timeframe, since, limit)
    assert isinstance(raw_tohlc_data, list)
    for item in raw_tohlc_data:
        assert len(item) == (6)
        assert isinstance(item[0], int)
        for val in item[1:]:
            assert isinstance(val, float)

    # catch bad (but almost good) symbol
    with pytest.raises(ValueError):
        raw_tohlc_data = safe_fetch_ohlcv(exch, "ETH-USDT", timeframe, since, limit)

    # it will catch type errors, except for exch. Test an example of this.
    with pytest.raises(TypeError):
        raw_tohlc_data = safe_fetch_ohlcv(exch, 11, timeframe, since, limit)
    with pytest.raises(TypeError):
        raw_tohlc_data = safe_fetch_ohlcv(exch, symbol, 11, since, limit)
    with pytest.raises(TypeError):
        raw_tohlc_data = safe_fetch_ohlcv(exch, symbol, timeframe, "f", limit)
    with pytest.raises(TypeError):
        raw_tohlc_data = safe_fetch_ohlcv(exch, symbol, timeframe, since, "f")

    # should not crash, just give warning
    safe_fetch_ohlcv("bad exch", symbol, timeframe, since, limit)
    safe_fetch_ohlcv(exch, "bad symbol", timeframe, since, limit)
    safe_fetch_ohlcv(exch, symbol, "bad timeframe", since, limit)
    safe_fetch_ohlcv(exch, symbol, timeframe, -5, limit)
    safe_fetch_ohlcv(exch, symbol, timeframe, since, -5)

    # ensure a None is returned when warning
    v = safe_fetch_ohlcv("bad exch", symbol, timeframe, since, limit)
    assert v is None
