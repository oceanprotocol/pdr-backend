import pytest
from enforce_typing import enforce_types

import requests_mock

from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv_dydx
from pdr_backend.util.time_types import UnixTimeMs


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
                "baseTokenVolume": "0.015",
            },
            {
                "startedAt": "2024-02-20T23:55:00.000Z",
                "open": "52324.0",
                "high": "52390.0",
                "low": "52223.0",
                "close": "52327.0",
                "baseTokenVolume": "0.015",
            },
            {
                "startedAt": "2024-02-21T00:00:00.000Z",
                "open": "52431.0",
                "high": "52431.0",
                "low": "52207.0",
                "close": "52348.0",
                "baseTokenVolume": "0.013",
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
            "https://indexer.v4testnet.dydx.exchange/v4/candles/perpetualMarkets/BTC-USD",
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
