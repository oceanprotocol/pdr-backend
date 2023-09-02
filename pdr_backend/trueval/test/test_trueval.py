from enforce_typing import enforce_types
from unittest.mock import patch

import pytest

from pdr_backend.trueval.main import get_trueval
from pdr_backend.models.feed import Feed


def mock_fetch_ohlcv(*args, **kwargs):
    since = kwargs.get("since")
    if since == 1000:
        return [[1000, 100], [2000, 200]]
    else:
        raise ValueError("Invalid timestamp")


def mock_fetch_ohlcv_fail(*args, **kwargs):
    return [[0, 0]]


@enforce_types
def test_get_trueval_success(monkeypatch):
    feed = Feed(
        name="ETH-USDT",
        address="0x1",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="eth-usdt",
        source="kraken",
        timeframe="5m",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    def mock_fetch_ohlcv(*args, **kwargs):
        since = kwargs.get("since")
        if since == 1:
            return [[None, 100]]
        elif since == 2:
            return [[None, 200]]
        else:
            raise ValueError("Invalid timestamp")

    monkeypatch.setattr("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv)


@enforce_types
def test_get_trueval_live_lowercase_slash_5m():
    feed = Feed(
        name="ETH-USDT",
        address="0x1",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="btc/usdt",
        source="kucoin",
        timeframe="5m",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    result = get_trueval(feed, 1692943200, 1692943200 + 5 * 60)
    assert result == (False, False)


@enforce_types
def test_get_trueval_live_lowercase_dash_1h():
    feed = Feed(
        name="ETH-USDT",
        address="0x1",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="btc-usdt",
        source="kucoin",
        timeframe="1h",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    result = get_trueval(feed, 1692943200, 1692943200 + 1 * 60 * 60)
    assert result == (False, False)


@enforce_types
def test_get_trueval_fail(monkeypatch):
    feed = Feed(
        name="ETH-USDT",
        address="0x1",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="eth-usdt",
        source="kraken",
        timeframe="5m",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    monkeypatch.setattr("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv_fail)

    with pytest.raises(Exception):
        result = get_trueval(feed, 1, 2)
        assert result == (False, True)  # 2nd True because failed
