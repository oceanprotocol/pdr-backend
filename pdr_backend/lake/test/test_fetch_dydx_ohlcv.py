import pytest
from enforce_typing import enforce_types

import requests_mock

from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv_dydx, fetch_dydx_data, transform_dydx_data_to_tuples
from pdr_backend.util.time_types import UnixTimeMs

from pdr_backend.util.constants import (
    CAND_USDCOINS,
    CAND_TIMEFRAMES,
)

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
                "baseTokenVolume": "None"
            },
            {
                "startedAt": "NaN",
                "open": "",
                "high": None,
                "low": "NaN",
                "close": "",
                "baseTokenVolume": "None"
            }
        ]
    }

@pytest.fixture
def mock_dydx_response():
    # Mocks expected api response
    return {
        "candles": [
            {
                "startedAt": "2024-02-20T23:50:00.000Z",
                "open": "52308.0",
                "high": "52394.0",
                "low": "52229.0",
                "close": "52394.0",
                "baseTokenVolume": "0.015"
            },
                        {
                "startedAt": "2024-02-20T23:55:00.000Z",
                "open": "52324.0",
                "high": "52390.0",
                "low": "52223.0",
                "close": "52327.0",
                "baseTokenVolume": "0.015"
            },
            {
                "startedAt": "2024-02-21T00:00:00.000Z",
                "open": "52431.0",
                "high": "52431.0",
                "low": "52207.0",
                "close": "52348.0",
                "baseTokenVolume": "0.013"
            },
        ]
    }

@enforce_types
def test_safe_fetch_ohlcv_dydx():

    start_date = UnixTimeMs.from_timestr("2024-02-21_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = "BTC-USD", "5MINS", start_date, end_date, 100

    # happy path
    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)
    assert result is not None
    assert len(result) == 300

def test_fetch_dydx_data_handles_nan_values(mock_nan_dydx_response):
    with requests_mock.Mocker() as m:
        m.get("https://indexer.v4testnet.dydx.exchange/v4/candles/perpetualMarkets/BTC-USD", json=mock_nan_dydx_response)

        start_date = UnixTimeMs.from_timestr("2024-02-20_23:50")
        end_date = UnixTimeMs.from_timestr("2024-02-20_23:55")
        symbol, resolution, st_ut, fin_ut, limit = "BTC-USD", "5MINS", start_date, end_date, 2

        result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

        assert result is not None and len(result) == 1
        assert all(isinstance(entry, tuple) for entry in result)

def test_bad_dydx_token():
    start_date = UnixTimeMs.from_timestr("2024-02-21_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = "RANDOMTOKEN-USD", "5MINS", start_date, end_date, 100

    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)

    assert 'errors' in result
    assert result is not None

    # TODO test bad token
    # TODO test bad start date or end date
    # TODO test bad limit

