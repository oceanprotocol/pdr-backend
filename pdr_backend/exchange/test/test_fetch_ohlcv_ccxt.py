from enforce_typing import enforce_types
import pytest

from pdr_backend.exchange.fetch_ohlcv_ccxt import fetch_ohlcv_ccxt
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
def test_ccxt_binanceus():
    _test_ccxt("binanceus")


@enforce_types
def test_ccxt_kraken():
    _test_ccxt("kraken")


@enforce_types
def _test_ccxt(exchange_str: str):
    since = UnixTimeMs.from_timestr("2023-06-18")
    pair_str, timeframe, limit = "ETH/USDT", "5m", 1000

    # happy path ccxt
    r = fetch_ohlcv_ccxt(exchange_str, pair_str, timeframe, since, limit)
    assert_raw_tohlc_data_ok(r)

    # catch type errors
    with pytest.raises(TypeError):
        fetch_ohlcv_ccxt(32, pair_str, timeframe, since, limit)
    with pytest.raises(TypeError):
        fetch_ohlcv_ccxt(exchange_str, 11, timeframe, since, limit)
    with pytest.raises(TypeError):
        fetch_ohlcv_ccxt(exchange_str, pair_str, 11, since, limit)
    with pytest.raises(TypeError):
        fetch_ohlcv_ccxt(exchange_str, pair_str, timeframe, "f", limit)
    with pytest.raises(TypeError):
        fetch_ohlcv_ccxt(exchange_str, pair_str, timeframe, since, "f")

    # catch value errors
    with pytest.raises(ValueError):
        fetch_ohlcv_ccxt("dydx", pair_str, timeframe, since, limit)
    with pytest.raises(ValueError):
        fetch_ohlcv_ccxt("bad exchange_str", pair_str, timeframe, since, limit)
    with pytest.raises(ValueError):
        fetch_ohlcv_ccxt(exchange_str, "bad-pair_str", timeframe, since, limit)
    with pytest.raises(ValueError):
        fetch_ohlcv_ccxt(exchange_str, "bad pair_str", timeframe, since, limit)
    with pytest.raises(ValueError):
        fetch_ohlcv_ccxt(exchange_str, pair_str, "bad timeframe", since, limit)


@enforce_types
def assert_raw_tohlc_data_ok(raw_tohlc_data):
    assert raw_tohlc_data, raw_tohlc_data
    assert isinstance(raw_tohlc_data, list)
    for item in raw_tohlc_data:
        assert len(item) == (6)
        assert isinstance(item[0], int)
        for val in item[1:]:
            assert isinstance(val, float)
