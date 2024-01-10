import ccxt
import pytest
from enforce_typing import enforce_types

from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv
from pdr_backend.util.timeutil import timestr_to_ut

EXCHS = [ccxt.binanceus(), ccxt.kraken()]


@enforce_types
@pytest.mark.parametrize("exch", EXCHS)
def test_safe_fetch_ohlcv(exch):
    since = timestr_to_ut("2023-06-18")
    symbol, timeframe, limit = "ETH/USDT", "5m", 1000

    # happy path
    raw_tohlc_data = safe_fetch_ohlcv(exch, symbol, timeframe, since, limit)
    assert_raw_tohlc_data_ok(raw_tohlc_data)

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


@enforce_types
def assert_raw_tohlc_data_ok(raw_tohlc_data):
    assert raw_tohlc_data, raw_tohlc_data
    assert isinstance(raw_tohlc_data, list)
    for item in raw_tohlc_data:
        assert len(item) == (6)
        assert isinstance(item[0], int)
        for val in item[1:]:
            assert isinstance(val, float)
