from typing import Any, Dict, List

from enforce_typing import enforce_types
import pytest
import requests_mock

from pdr_backend.lake.constants import BASE_URL_DYDX
from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv_dydx
from pdr_backend.util.time_types import UnixTimeMs

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
            "msg": "resolution must be a valid Candle Resolution, "
            "one of 1MIN,5MINS,...",
            "param": "resolution",
            "location": "params",
        }
    ]
}

mock_bad_date_dydx_response: Dict[str, List[Any]] = {"candles": []}

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


@pytest.mark.parametrize(
    "symbol, timeframe, since, limit, expected_timestamp,"
    + " expected_close, expected_error_msg, mock_response",
    [
        (
            "BTC-USD",
            "5m",
            UnixTimeMs.from_timestr("2024-02-27"),
            1,
            1709139000000,
            61800,
            None,
            mock_dydx_response,
        ),
        (
            "BTC-ETH",
            "5m",
            UnixTimeMs.from_timestr("2024-02-27"),
            1,
            None,
            None,
            "ticker must be a valid ticker (BTC-USD, etc)",
            mock_bad_token_dydx_response_1,
        ),
        (
            "RANDOMTOKEN-USD",
            "5m",
            UnixTimeMs.from_timestr("2024-02-27"),
            1,
            None,
            None,
            "ticker must be a valid ticker (BTC-USD, etc)",
            mock_bad_token_dydx_response_2,
        ),
        (
            "BTC-USD",
            "5MINS",
            UnixTimeMs.from_timestr("2024-02-27"),
            1,
            None,
            None,
            "resolution must be a valid Candle Resolution," + " one of 1MIN,5MINS,...",
            mock_bad_timeframe_dydx_response,
        ),
        (
            "BTC-USD",
            "5MINS",
            UnixTimeMs.from_timestr("2222-02-27"),
            1,
            None,
            None,
            None,
            mock_bad_date_dydx_response,
        ),
        (
            "BTC-USD",
            "5MINS",
            UnixTimeMs.from_timestr("2024-02-27"),
            100000,
            None,
            None,
            "limit must be a positive integer that is not greater than max: 100",
            mock_bad_limit_dydx_response,
        ),
    ],
)
@enforce_types
def test_safe_fetch_ohlcv_dydx(
    symbol,
    timeframe,
    since,
    limit,
    expected_timestamp,
    expected_close,
    expected_error_msg,
    mock_response,
):
    with requests_mock.Mocker() as m:
        m.register_uri(
            "GET",
            f"{BASE_URL_DYDX}/{symbol}?resolution={timeframe}"
            f"&fromISO={since.to_iso_timestr()}&limit={limit}",
            json=mock_response,
        )
        result = safe_fetch_ohlcv_dydx(symbol, timeframe, since, limit)

        if expected_timestamp:
            assert result[0][0] == expected_timestamp, "Timestamp does not match"
            assert result[0][4] == expected_close, "Close price does not match"
        elif expected_error_msg:
            assert (
                "msg" in result[0][1] and result[0][1][1] == expected_error_msg
            ), "Expected an error message"
        else:
            assert result is None
