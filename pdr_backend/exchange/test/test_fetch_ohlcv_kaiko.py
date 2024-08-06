from unittest.mock import patch

import pytest
from pdr_backend.exchange.fetch_ohlcv_kaiko import (
    convert_to_tohlcv,
    exchange_str_to_kaiko,
    fetch_ohlcv_kaiko,
)
from pdr_backend.util.time_types import UnixTimeMs


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return {"data": self.json_data}


mock_kaiko_data = [
    {
        "timestamp": 1722940167000,
        "open": "55214",
        "high": "55214",
        "low": "55214",
        "close": "55214",
        "volume": "0.00728",
    },
    {
        "timestamp": 1722940168000,
        "open": "55220",
        "high": "55230",
        "low": "55210",
        "close": "55225",
        "volume": "0.00850",
    },
]


def test_exchange_str_to_kaiko():
    assert exchange_str_to_kaiko("binance") == "binc"
    assert exchange_str_to_kaiko("unknown_exchange") == "unknown_exchange"


def test_convert_to_tohlcv():
    raw_tohlcv_data = convert_to_tohlcv(mock_kaiko_data)
    print(raw_tohlcv_data)
    assert raw_tohlcv_data[0] == (
        1722940167000,
        55214.0,
        55214.0,
        55214.0,
        55214.0,
        0.00728,
    )


def test_fetch_ohlcv_kaiko_key_error():
    exchange_str = "binc"
    pair_str = "btc-usdt"
    timeframe = "1h"
    since = UnixTimeMs(1722940167000)
    limit = 1000

    mock_response = MockResponse(mock_kaiko_data, 200)
    with patch("requests.get", return_value=mock_response):
        with pytest.raises(ValueError):
            fetch_ohlcv_kaiko(exchange_str, pair_str, timeframe, since, limit)


def test_fetch_ohlcv_kaiko_success(monkeypatch):
    exchange_str = "binc"
    pair_str = "btc-usdt"
    timeframe = "1h"
    since = UnixTimeMs(1722940167000)
    limit = 1000

    # mock env KAIKO_KEY
    monkeypatch.setenv("KAIKO_KEY", "dummy_key")

    mock_response = MockResponse(mock_kaiko_data, 200)
    with patch("requests.get", return_value=mock_response):
        result = fetch_ohlcv_kaiko(exchange_str, pair_str, timeframe, since, limit)
        assert result[0] == (
            1722940167000,
            55214.0,
            55214.0,
            55214.0,
            55214.0,
            0.00728,
        )
