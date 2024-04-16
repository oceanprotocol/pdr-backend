from enforce_typing import enforce_types
import pytest
import requests_mock

from pdr_backend.exchange.constants import BASE_URL_DYDX
from pdr_backend.exchange.fetch_ohlcv_dydx import (
    fetch_ohlcv_dydx,
    _dydx_ticker,
    _dydx_resolution,
    _float_or_none,
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


@pytest.mark.skip(reason="Unskip once #879 is fixed")
@enforce_types
def test_dydx__real_response__fromISO_issue_879():
    # setup problem: 'tsince'
    tsince_iso_str = "2024-02-27_00:00:00.000"
    tsince_UnixTimeMs = UnixTimeMs.from_timestr(tsince_iso_str)
    assert tsince_UnixTimeMs == 1708992000000
    assert tsince_UnixTimeMs.to_timestr() == tsince_iso_str

    # setup problem: the rest
    symbol = "BTC/USD"
    timeframe = "5m"
    limit = 1

    # get result
    raw_tohlcv_data = fetch_ohlcv_dydx(symbol, timeframe, tsince_UnixTimeMs, limit)
    tohlcv = raw_tohlcv_data[0]

    # dydx api doesn't properly address fromISO. We must fix this, see #879
    t = tohlcv[0]
    t_UnixTimeMs = UnixTimeMs(t)
    t_iso_str = t_UnixTimeMs.to_iso_timestr()  # bad eg '2024-04-16T00:25:00.000Z'
    assert t_iso_str == tsince_iso_str
    assert t_UnixTimeMs == tsince_UnixTimeMs

    # when #879 fixed, add proper vals here
    # ohlcv = tohlcv[1:]
    # assert ohlcv == (fix me val, ..)


@enforce_types
def test_dydx__bad_paths():
    # setup problem
    symbol = "BTC/USD"
    timeframe = "5m"
    since = UnixTimeMs.from_timestr("2024-02-27_00:00:00.000")
    limit = 1

    # bad symbol
    bad_symbol = "BTC-USD"
    with pytest.raises(ValueError):
        _ = fetch_ohlcv_dydx(bad_symbol, timeframe, since, limit)

    # bad timeframe: should be eg "5m"
    bad_timeframe = "5MINS"
    with pytest.raises(ValueError):
        _ = fetch_ohlcv_dydx(symbol, bad_timeframe, since, limit)


@enforce_types
def test_dydx_ticker():
    # happy path
    assert _dydx_ticker("BTC/USDT") == "BTC-USDT"

    # bad paths
    with pytest.raises(ValueError):
        _ = _dydx_ticker("BTC-USDT")


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
