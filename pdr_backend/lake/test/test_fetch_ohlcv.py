import ccxt
from datetime import datetime, timedelta, timezone
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.lake.fetch_ohlcv import (
    safe_fetch_ohlcv_ccxt,
    safe_fetch_ohlcv_dydx,
    clean_raw_ohlcv,
)
from pdr_backend.util.time_types import UnixTimeMs


MPE = 300000  # ms per 5min epoch
T4, T5, T6, T7, T8, T10 = 4 * MPE, 5 * MPE, 6 * MPE, 7 * MPE, 8 * MPE, 10 * MPE

#       ut  #o   #h  #l    #c   #v
RAW5 = [T5, 0.5, 12, 0.12, 1.1, 7.0]
RAW6 = [T6, 0.5, 11, 0.11, 2.2, 7.0]
RAW7 = [T7, 0.5, 10, 0.10, 3.3, 7.0]
RAW8 = [T8, 0.5, 9, 0.09, 4.4, 7.0]


@enforce_types
def test_clean_raw_ohlcv():
    feed = ArgFeed("binanceus", None, "ETH/USDT", "5m")

    assert clean_raw_ohlcv(None, feed, UnixTimeMs(0), UnixTimeMs(0)) == []
    assert clean_raw_ohlcv([], feed, UnixTimeMs(0), UnixTimeMs(0)) == []

    # RAW5v is the shape of "raw_tohlcv_data" with just one candle
    RAW5v = [RAW5]
    assert clean_raw_ohlcv(RAW5v, feed, UnixTimeMs(0), UnixTimeMs(0)) == []
    assert clean_raw_ohlcv(RAW5v, feed, UnixTimeMs(0), UnixTimeMs(T4)) == []
    assert clean_raw_ohlcv(RAW5v, feed, UnixTimeMs(T6), UnixTimeMs(T10)) == []
    assert clean_raw_ohlcv(RAW5v, feed, UnixTimeMs(T5), UnixTimeMs(T5)) == RAW5v
    assert clean_raw_ohlcv(RAW5v, feed, UnixTimeMs(0), UnixTimeMs(T10)) == RAW5v
    assert clean_raw_ohlcv(RAW5v, feed, UnixTimeMs(0), UnixTimeMs(T5)) == RAW5v
    assert clean_raw_ohlcv(RAW5v, feed, UnixTimeMs(T5), UnixTimeMs(T10)) == RAW5v

    # RAW5v is the shape of "raw_tohlcv_data" with four candles
    RAW5678v = [RAW5, RAW6, RAW7, RAW8]
    assert clean_raw_ohlcv(RAW5678v, feed, UnixTimeMs(0), UnixTimeMs(0)) == []
    assert clean_raw_ohlcv(RAW5678v, feed, UnixTimeMs(0), UnixTimeMs(T10)) == RAW5678v
    assert clean_raw_ohlcv(RAW5678v, feed, UnixTimeMs(T5), UnixTimeMs(T5)) == [RAW5]
    assert clean_raw_ohlcv(RAW5678v, feed, UnixTimeMs(T6), UnixTimeMs(T6)) == [RAW6]
    assert clean_raw_ohlcv(RAW5678v, feed, UnixTimeMs(T5), UnixTimeMs(T6)) == [
        RAW5,
        RAW6,
    ]
    assert clean_raw_ohlcv(RAW5678v, feed, UnixTimeMs(T5), UnixTimeMs(T8)) == RAW5678v
    assert clean_raw_ohlcv(RAW5678v, feed, UnixTimeMs(T7), UnixTimeMs(T8)) == [
        RAW7,
        RAW8,
    ]
    assert clean_raw_ohlcv(RAW5678v, feed, UnixTimeMs(T8), UnixTimeMs(T8)) == [RAW8]


@enforce_types
@pytest.mark.parametrize("exch", [ccxt.binanceus(), ccxt.kraken()])
def test_safe_fetch_ohlcv(exch):
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

    # happy path dydx
    fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
    symbol, timeframe, since, limit = (
        "BTC-USD",
        "5MINS",
        UnixTimeMs.from_dt(fifteen_min_ago),
        100,
    )
    result = safe_fetch_ohlcv_dydx("dydx", symbol, timeframe, since, limit)
    assert_safe_fetch_ohlcv_dydx_ok(result)


@enforce_types
def assert_raw_tohlc_data_ok(raw_tohlc_data):
    assert raw_tohlc_data, raw_tohlc_data
    assert isinstance(raw_tohlc_data, list)
    for item in raw_tohlc_data:
        assert len(item) == (6)
        assert isinstance(item[0], int)
        for val in item[1:]:
            assert isinstance(val, float)


@enforce_types
def assert_safe_fetch_ohlcv_dydx_ok(result):
    # Result should return one list called 'candles' that contains 3 lists of 100 candles data
    assert result is not None
    assert len(result) == 1
    assert len(result["candles"]) == 3
