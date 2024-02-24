import ccxt
import pytest
import requests_mock
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

    # happy path
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


@pytest.fixture
def mock_nan_dydx_response():
    # Mocks NaN or missing value api responses -- convention is not clear from api docs
    return {
        "candles": [
            {
                "startedAt": "2024-02-21T00:00:00.000Z",
                "open": "",
                "high": None,
                "low": "NaN",
                "close": "",
                "baseTokenVolume": "None",
            },
            {
                "startedAt": "NaN",
                "open": "",
                "high": None,
                "low": "NaN",
                "close": "",
                "baseTokenVolume": "None",
            },
        ]
    }


@enforce_types
def test_safe_fetch_ohlcv_dydx():
    # test happy path
    start_date = UnixTimeMs.from_timestr("2024-02-21_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = (
        "BTC-USD",
        "5MINS",
        start_date,
        end_date,
        100,
    )

    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)
    assert result is not None
    assert len(result) == 300


def test_fetch_dydx_data_handles_nan_values(mock_nan_dydx_response):
    # test nan values are handled gracefully
    with requests_mock.Mocker() as m:
        m.get(
            "https://indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-USD",
            json=mock_nan_dydx_response,
        )

        start_date = UnixTimeMs.from_timestr("2024-02-20_23:50")
        end_date = UnixTimeMs.from_timestr("2024-02-20_23:55")
        symbol, resolution, st_ut, fin_ut, limit = (
            "BTC-USD",
            "5MINS",
            start_date,
            end_date,
            2,
        )

        result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

        assert result is not None and len(result) == 1
        assert all(isinstance(entry, tuple) for entry in result)


def test_dydx_token_does_not_exist():
    # test token must exist
    start_date = UnixTimeMs.from_timestr("2024-02-21_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = (
        "RANDOMTOKEN-USD",
        "5MINS",
        start_date,
        end_date,
        100,
    )

    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

    assert "errors" in result
    assert result is not None


def test_bad_dydx_token_pair():
    # test pair ends with 'USD' -- cannot be USDC, USDT, DAI, or any other coins
    start_date = UnixTimeMs.from_timestr("2024-02-21_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = (
        "BTC-ETH",
        "5MINS",
        start_date,
        end_date,
        100,
    )

    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

    assert "errors" in result
    assert result is not None


def test_bad_dydx_limit():
    # test limit must be an int > 0 && <= 100
    start_date = UnixTimeMs.from_timestr("2024-02-21_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = (
        "BTC-USD",
        "5MINS",
        start_date,
        end_date,
        1000,
    )

    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

    assert "errors" in result
    assert result is not None


def test_bad_dydx_resolution():
    # test resolution must be "1MIN", "5MINS", "15MINS", "30MINS", "1HOUR", or "1DAY"
    start_date = UnixTimeMs.from_timestr("2024-02-21_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = (
        "BTC-USD",
        "123minutes",
        start_date,
        end_date,
        1000,
    )

    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

    assert result is None


def test_bad_dydx_start_date():
    # test start date must be earlier than end date
    start_date = UnixTimeMs.from_timestr("2024-02-22_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = (
        "BTC-USD",
        "5MINS",
        start_date,
        end_date,
        1000,
    )

    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

    assert result is None


def test_dydx_start_date_before_now():
    # test start date must be earlier than now
    start_date = UnixTimeMs.from_timestr("2222-02-22_00:00")
    end_date = UnixTimeMs.from_timestr("2222-02-22_00:15")
    symbol, resolution, st_ut, fin_ut, limit = (
        "BTC-USD",
        "5MINS",
        start_date,
        end_date,
        1000,
    )

    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

    assert result is None
