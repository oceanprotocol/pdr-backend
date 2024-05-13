from datetime import datetime, timedelta
from enforce_typing import enforce_types

import pytest
import requests_mock

from pdr_backend.exchange.constants import BASE_URL_DYDX
from pdr_backend.exchange.fetch_ohlcv_dydx import (
    fetch_ohlcv_dydx,
    _dydx_ticker,
    _dydx_resolution,
    _float_or_none,
    _time_delta_from_timeframe,
)
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
def test_dydx__mocked_response():
    # setup problem
    symbol = "BTC/USD"
    timeframe = "5m"
    since = UnixTimeMs.from_timestr("2024-02-27_00:00:00.000")
    limit = 1

    mock_response_data = {
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

    # get result
    with requests_mock.Mocker() as m:
        ticker = _dydx_ticker(symbol)
        resolution = _dydx_resolution(timeframe)
        fromISO = since.to_iso_timestr()
        m.register_uri(
            "GET",
            f"{BASE_URL_DYDX}/candles/perpetualMarkets/{ticker}"
            f"?resolution={resolution}&fromISO={fromISO}&limit={limit}",
            json=mock_response_data,
        )
        raw_tohlcv_data = fetch_ohlcv_dydx(symbol, timeframe, since, limit)

    # test results
    tohlcv = raw_tohlcv_data[0]
    assert len(tohlcv) == 6
    # t = tohlcv[0]
    # assert t == 1709135400000 # fix & uncomment as part of #879
    ohlcv = tohlcv[1:]
    assert ohlcv == (61840, 61848, 61687, 61800, 23.6064)


@enforce_types
def test_dydx__real_response__basic():
    # setup problem
    symbol = "BTC/USD"
    timeframe = "5m"
    since = UnixTimeMs.from_timestr("2024-02-27_00:00:00.000")
    limit = 1

    # get result
    raw_tohlcv_data = fetch_ohlcv_dydx(symbol, timeframe, since, limit)

    # test results
    tohlcv = raw_tohlcv_data[0]
    assert len(tohlcv) == 6


@enforce_types
def test_dydx__real_response__fromISO():
    # setup problem: 'tsince'
    tsince_iso_str = "2024-02-27_00:00:00.000"
    tsince_UnixTimeMs = UnixTimeMs.from_timestr(tsince_iso_str)
    assert tsince_UnixTimeMs == 1708992000000
    assert tsince_UnixTimeMs.to_timestr() == tsince_iso_str

    # setup problem: the rest
    symbol = "BTC/USD"
    timeframe = "5m"
    limit = 10

    # get result
    raw_tohlcv_data = fetch_ohlcv_dydx(symbol, timeframe, tsince_UnixTimeMs, limit)

    assert len(raw_tohlcv_data) == 10, "Length must be 10, limit is 10"

    # First timestamp is expected to be:
    # 2024-02-27T00:00:00.000Z
    dt = datetime.fromisoformat("2024-02-27T00:00:00.000")
    unix_ms = dt.timestamp() * 1e3
    assert (
        raw_tohlcv_data[0][0] == unix_ms
    ), f"Expected {unix_ms}, got {raw_tohlcv_data[0][0]}"

    # Last timestamp is expected to be:
    # 2024-02-27T00:45:00.000Z
    dt = datetime.fromisoformat("2024-02-27T00:45:00.000")
    unix_ms = dt.timestamp() * 1e3
    assert (
        raw_tohlcv_data[-1][0] == unix_ms
    ), f"Expected {unix_ms}, got {raw_tohlcv_data[-1][0]}"

    # Price checks
    assert raw_tohlcv_data[0][1] == 54541.0
    assert raw_tohlcv_data[0][2] == 54661.0
    assert raw_tohlcv_data[1][4] == 54691.0
    assert raw_tohlcv_data[-1][3] == 54545.0


@enforce_types
def test_dydx__bad_paths():
    # setup problem
    symbol = "BTC/USD"
    since = UnixTimeMs.from_timestr("2024-02-27_00:00:00.000")
    limit = 1

    # bad timeframe: should be eg "5m"
    bad_timeframe = "5MINS"
    with pytest.raises(ValueError):
        _ = fetch_ohlcv_dydx(symbol, bad_timeframe, since, limit)


@enforce_types
def test_dydx_ticker():
    assert _dydx_ticker("BTC/USDT") == "BTC-USD"


@enforce_types
def test_dydx_resolution():
    # happy path
    assert _dydx_resolution("5m") == "5MINS"
    assert _dydx_resolution("1h") == "1HOUR"

    # currently-unsupported; add support as needed
    with pytest.raises(ValueError):
        _ = _dydx_resolution("1m")
    with pytest.raises(ValueError):
        _ = _dydx_resolution("15m")

    # bad paths
    with pytest.raises(ValueError):
        _ = _dydx_resolution("5MINS")

    with pytest.raises(ValueError):
        _ = _dydx_resolution("foo")


@enforce_types
def test_fetch_ohlcv_float_or_none():
    # happy paths
    assert _float_or_none("3.2") == 3.2
    assert _float_or_none(None) is None

    # bad paths
    with pytest.raises(TypeError):
        _ = _float_or_none(3.2)
    with pytest.raises(TypeError):
        _ = _float_or_none(3)
    with pytest.raises(ValueError):
        _ = _float_or_none("foo")


def test_time_delta_from_valid_timeframes():
    test_cases = [
        ("5m", 1, timedelta(seconds=300 * 1)),
        ("5m", 10, timedelta(seconds=300 * 10)),
        ("5m", 25, timedelta(seconds=300 * 25)),
        ("5m", 500, timedelta(seconds=300 * 500)),
        ("1h", 1, timedelta(seconds=3600 * 1)),
        ("1h", 5, timedelta(seconds=3600 * 5)),
        ("1h", 42, timedelta(seconds=3600 * 42)),
    ]

    for timeframe, limit, expected in test_cases:
        assert (
            _time_delta_from_timeframe(timeframe, limit) == expected
        ), f"Failed for timeframe={timeframe}"


def test_time_delta_from_invalid_timeframe():
    with pytest.raises(ValueError) as excinfo:
        _time_delta_from_timeframe("1hh", 1)
    assert "Don't currently support timeframe=1hh" in str(excinfo.value)
