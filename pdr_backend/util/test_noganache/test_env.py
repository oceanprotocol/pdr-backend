from unittest.mock import patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.util.env import getenv_or_exit, parse_filters


@enforce_types
def test_getenv_or_exit(monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    with pytest.raises(SystemExit):
        getenv_or_exit("RPC_URL")

    monkeypatch.setenv("RPC_URL", "http://test.url")
    assert getenv_or_exit("RPC_URL") == "http://test.url"


@enforce_types
def test_parse_filters():
    mock_values = {
        "PAIR_FILTER": "BTC-USDT,ETH-USDT",
        "TIMEFRAME_FILTER": "1D,1H",
        "SOURCE_FILTER": None,
        "OWNER_ADDRS": "0x1234,0x5678",
    }

    def mock_getenv(key, default=None):
        return mock_values.get(key, default)

    with patch("pdr_backend.util.env.getenv", mock_getenv):
        result = parse_filters()

    expected = (
        ["BTC-USDT", "ETH-USDT"],  # pair
        ["1D", "1H"],  # timeframe
        [],  # source
        ["0x1234", "0x5678"],  # owner_addrs
    )

    assert result == expected, f"Expected {expected}, but got {result}"
