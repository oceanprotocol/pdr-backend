from datetime import datetime
from typing import Any, Dict, List, Union

import ccxt
from enforce_typing import enforce_types
import polars as pl
import pytest
import requests_mock

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.lake.fetch_ohlcv import (
    _cast_uts_to_int,
    _filter_within_timerange,
    _ohlcv_to_uts,
    clean_raw_ohlcv,
    safe_fetch_ohlcv_ccxt,
    safe_fetch_ohlcv_dydx,
)
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.constants import TOHLCV_SCHEMA_PL


MPE = 300000  # ms per 5min epoch
T4, T5, T6, T7, T8, T10 = 4 * MPE, 5 * MPE, 6 * MPE, 7 * MPE, 8 * MPE, 10 * MPE

#       ut  #o   #h  #l    #c   #v
RAW5 = [T5, 0.5, 12, 0.12, 1.1, 7.0]
RAW6 = [T6, 0.5, 11, 0.11, 2.2, 7.0]
RAW7 = [T7, 0.5, 10, 0.10, 3.3, 7.0]
RAW8 = [T8, 0.5, 9, 0.09, 4.4, 7.0]

mock_dydx_response = {
    "candles": [
        {
            "startedAt": "2024-02-28T16:50:00.000Z",
            "ticker": "BTC-USD",
            "resolution": "5MINS",
            "open": "61840",
            "high": "61848",
            "low": "61687",
            "close": "61800",
            "baseTokenVolume": "23.6064",
            "usdVolume": "1458183.4133",
            "trades": 284,
            "startingOpenInterest": "504.4262",
        }
    ]
}

mock_bad_token_dydx_response_1 = {
    "errors": [
        {
            "value": "BTC-ETH",
            "msg": "ticker must be a valid ticker (BTC-USD, etc)",
            "param": "ticker",
            "location": "params",
        }
    ]
}

mock_bad_token_dydx_response_2 = {
    "errors": [
        {
            "value": "RANDOMTOKEN-USD",
            "msg": "ticker must be a valid ticker (BTC-USD, etc)",
            "param": "ticker",
            "location": "params",
        }
    ]
}

mock_bad_timeframe_dydx_response = {
    "errors": [
        {
            "value": "5m",
            "msg": "resolution must be a valid Candle Resolution, one of 1MIN,5MINS,15MINS,30MINS,1HOUR,4HOURS,1DAY",
            "param": "resolution",
            "location": "params",
        }
    ]
}

mock_bad_date_dydx_response: Dict[str, List[Any]] = {
    "candles": []
}  # Added variable annotation to resolve mypy inferred typing issue

mock_bad_limit_dydx_response = {
    "errors": [
        {
            "value": "100000",
            "msg": "limit must be a positive integer that is not greater than max: 100",
            "param": "limit",
            "location": "params",
        }
    ]
}


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
def test_safe_fetch_ohlcv_ccxt(exch):
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
def test_safe_fetch_ohlcv_dydx():

    # happy path dydx
    with requests_mock.Mocker() as m:
        m.register_uri(
            "GET",
            "https://indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-USD?resolution=5MINS&fromISO=2024-02-27T00:00:00.000Z&limit=1",
            json=mock_dydx_response,
        )
        exch, symbol, timeframe, since, limit = (
            "dydx",
            "BTC-USD",
            "5MINS",
            UnixTimeMs.from_timestr("2024-02-27"),
            1,
        )
        result = safe_fetch_ohlcv_dydx(exch, symbol, timeframe, since, limit)

        assert result[0][0] == 1709157000000, "Timestamp does not match"
        assert result[0][1] == 61840, "Open value does not match"
        assert result[0][2] == 61848, "High value does not match"
        assert result[0][3] == 61687, "Low value does not match"
        assert result[0][4] == 61800, "Close value does not match"
        assert result[0][5] == 23.6064, "Volume does not match"

    # bad token test 1 - pair must end in "-USD"
    with requests_mock.Mocker() as m:
        m.register_uri(
            "GET",
            "https://indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-ETH?resolution=5MINS&fromISO=2024-02-27T00:00:00.000Z&limit=1",
            json=mock_bad_token_dydx_response_1,
        )
        exch, symbol, timeframe, since, limit = (
            "dydx",
            "BTC-ETH",
            "5MINS",
            UnixTimeMs.from_timestr("2024-02-27"),
            1,
        )
        result = safe_fetch_ohlcv_dydx(exch, symbol, timeframe, since, limit)
        assert result[0][1] == ("msg", "ticker must be a valid ticker (BTC-USD, etc)")

    # bad token test 2 - token must exist
    with requests_mock.Mocker() as m:
        m.register_uri(
            "GET",
            "https://indexer.dydx.trade/v4/candles/perpetualMarkets/RANDOMTOKEN-USD?resolution=5MINS&fromISO=2024-02-27T00:00:00.000Z&limit=1",
            json=mock_bad_token_dydx_response_2,
        )
        exch, symbol, timeframe, since, limit = (
            "dydx",
            "RANDOMTOKEN-USD",
            "5MINS",
            UnixTimeMs.from_timestr("2024-02-27"),
            1,
        )
        result = safe_fetch_ohlcv_dydx(exch, symbol, timeframe, since, limit)
        assert result[0][1] == ("msg", "ticker must be a valid ticker (BTC-USD, etc)")

    # bad timeframe test
    with requests_mock.Mocker() as m:
        m.register_uri(
            "GET",
            "https://indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-USD?resolution=5m&fromISO=2024-02-27T00:00:00.000Z&limit=1",
            json=mock_bad_timeframe_dydx_response,
        )
        exch, symbol, timeframe, since, limit = (
            "dydx",
            "BTC-USD",
            "5m",
            UnixTimeMs.from_timestr("2024-02-27"),
            1,
        )
        result = safe_fetch_ohlcv_dydx(exch, symbol, timeframe, since, limit)
        assert result[0][1] == (
            "msg",
            "resolution must be a valid Candle Resolution, one of 1MIN,5MINS,15MINS,30MINS,1HOUR,4HOURS,1DAY",
        )

    # bad date test
    with requests_mock.Mocker() as m:
        m.register_uri(
            "GET",
            "https://indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-USD?resolution=5MINS&fromISO=2222-02-27T00:00:00.000Z&limit=1",
            json=mock_bad_date_dydx_response,
        )
        exch, symbol, timeframe, since, limit = (
            "dydx",
            "BTC-USD",
            "5MINS",
            UnixTimeMs.from_timestr("2222-02-27"),
            1,
        )
        result = safe_fetch_ohlcv_dydx(exch, symbol, timeframe, since, limit)
        assert result == []

    # bad limit test
    with requests_mock.Mocker() as m:
        m.register_uri(
            "GET",
            "https://indexer.dydx.trade/v4/candles/perpetualMarkets/BTC-USD?resolution=5MINS&fromISO=2024-02-27T00:00:00.000Z&limit=100000",
            json=mock_bad_limit_dydx_response,
        )
        exch, symbol, timeframe, since, limit = (
            "dydx",
            "BTC-USD",
            "5MINS",
            UnixTimeMs.from_timestr("2024-02-27"),
            100000,
        )
        result = safe_fetch_ohlcv_dydx(exch, symbol, timeframe, since, limit)
        assert result[0][1] == (
            "msg",
            "limit must be a positive integer that is not greater than max: 100",
        )


@enforce_types
def assert_raw_tohlc_data_ok(raw_tohlc_data):
    assert raw_tohlc_data, raw_tohlc_data
    assert isinstance(raw_tohlc_data, list)
    for item in raw_tohlc_data:
        assert len(item) == (6)
        assert isinstance(item[0], int)
        for val in item[1:]:
            assert isinstance(val, float)


def test_schema_interpreter_float_as_integer():
    tohlcv_data = [
        [1624003200000, 1624003500000, 1624003800000, 1624004100000, 1624004400000],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
    ]

    # First DataFrame creation (should pass)
    tohlcv_df = pl.DataFrame(tohlcv_data, schema=TOHLCV_SCHEMA_PL)
    assert isinstance(tohlcv_df, pl.DataFrame)

    # Try to create DataFrame with floating-point decimal timestamp instead of integer
    try:
        tohlcv_data = [
            [
                1624003200000.00,
                1624003500000,
                1624003800000,
                1624004100000,
                1624004400000,
            ],
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [1.0, 2.0, 3.0, 4.0, 5.0],
        ]
        tohlcv_df = pl.DataFrame(tohlcv_data, schema=TOHLCV_SCHEMA_PL)
    except TypeError as e:
        # Timestamp written as a float "1624003200000.00" raises error
        assert str(e) == "'float' object cannot be interpreted as an integer"


def test_fix_schema_interpreter_float_as_integer():
    # Use clean_raw_ohlcv to affix timestamp as int
    # Then turn into dataframe
    T1 = 1624003200000
    RAW_TOHLCV = [float(T1), 0.5, 12, 0.12, 1.1, 7.0]

    uts = _ohlcv_to_uts([RAW_TOHLCV])
    assert type(uts[0]) == float

    uts = _cast_uts_to_int(uts)
    assert type(uts[0]) == int

    tohlcv_data = _filter_within_timerange([RAW_TOHLCV], UnixTimeMs(T1), UnixTimeMs(T1))
    tohlcv_df = pl.DataFrame(tohlcv_data, schema=TOHLCV_SCHEMA_PL)
    assert isinstance(tohlcv_df, pl.DataFrame)
