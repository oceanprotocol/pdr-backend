from enforce_typing import enforce_types

import pytest

from pdr_backend.trueval.get_trueval import get_trueval
from pdr_backend.models.feed import mock_feed

_PATH = "pdr_backend.trueval.get_trueval"


@enforce_types
def test_get_trueval_success(monkeypatch):
    def mock_fetch_ohlcv(*args, **kwargs):  # pylint: disable=unused-argument
        since = kwargs.get("since")
        if since == 0:
            return [[0, 0, 0, 0, 100], [300000, 0, 0, 0, 200]]
        raise ValueError(f"Invalid timestamp: since={since}")

    monkeypatch.setattr(f"{_PATH}.safe_fetch_ohlcv", mock_fetch_ohlcv)

    feed = mock_feed("5m", "kraken", "ETH/USDT")

    init_ts = feed.seconds_per_epoch
    end_ts = init_ts + feed.seconds_per_epoch
    result = get_trueval(feed, init_ts, end_ts)
    assert result == (True, False)


@enforce_types
def test_get_trueval_fail(monkeypatch):
    def mock_fetch_ohlcv_fail(*args, **kwargs):  # pylint: disable=unused-argument
        return [[0, 0, 0, 0, 0], [300000, 0, 0, 0, 200]]

    monkeypatch.setattr(f"{_PATH}.safe_fetch_ohlcv", mock_fetch_ohlcv_fail)

    feed = mock_feed("5m", "kraken", "eth-usdt")

    init_ts = feed.seconds_per_epoch
    end_ts = init_ts + feed.seconds_per_epoch
    with pytest.raises(Exception):
        result = get_trueval(feed, init_ts, end_ts)
        assert result == (False, True)  # 2nd True because failed
