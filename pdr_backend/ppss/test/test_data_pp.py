from enforce_typing import enforce_types
import pytest

from pdr_backend.models.feed import mock_feed
from pdr_backend.ppss.data_pp import DataPP, mock_data_pp


@enforce_types
def test_data_pp_1feed():
    pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["kraken h ETH/USDT"],
            "sim_only": {"test_n": 2},
        }
    )

    # yaml properties
    assert isinstance(pp.timeframe, str)
    assert pp.predict_feeds_strs == ["kraken h ETH/USDT"]
    assert pp.test_n == 2

    # derivative properties
    assert isinstance(pp.timeframe_ms, int)  # test more below
    assert isinstance(pp.timeframe_m, int)  # ""
    assert pp.predict_feed_tups == [("kraken", "high", "ETH/USDT")]
    assert pp.pair_strs == ["ETH/USDT"]
    assert pp.exchange_strs == ["kraken"]
    assert pp.predict_feed_tup == ("kraken", "high", "ETH/USDT")
    assert pp.exchange_str == "kraken"
    assert pp.signal_str == "high"
    assert pp.pair_str == "ETH/USDT"
    assert pp.base_str == "ETH"
    assert pp.quote_str == "USDT"

    # str
    assert "DataPP" in str(pp)

    # setters
    pp.set_timeframe("1h")
    assert pp.timeframe == "1h"
    pp.set_predict_feeds(["binance oh BTC/DAI"])
    assert pp.predict_feeds_strs == ["binance oh BTC/DAI"]


@enforce_types
def test_data_pp_3feeds():
    pp = mock_data_pp("5m", ["kraken h ETH/USDT", "binance oh BTC/USDT"])

    # yaml properties
    assert pp.timeframe == "5m"
    assert pp.predict_feeds_strs == ["kraken h ETH/USDT", "binance oh BTC/USDT"]

    # derivative properties
    assert pp.predict_feed_tups == [
        ("kraken", "high", "ETH/USDT"),
        ("binance", "open", "BTC/USDT"),
        ("binance", "high", "BTC/USDT"),
    ]
    assert pp.pair_strs == ["ETH/USDT", "BTC/USDT"]
    assert pp.exchange_strs == ["kraken", "binance"]
    with pytest.raises(ValueError):
        pp.predict_feed_tup  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.exchange_str  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.signal_str  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.pair_str  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.base_str  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.quote_str  # pylint: disable=pointless-statement


@enforce_types
def test_pp_5m_vs_1h():
    pp = mock_data_pp("5m", ["binance c ETH/USDT"])
    assert pp.timeframe == "5m"
    assert pp.timeframe_ms == 5 * 60 * 1000
    assert pp.timeframe_s == 5 * 60
    assert pp.timeframe_m == 5

    # 1h
    pp = mock_data_pp("1h", ["binance c ETH/USDT"])
    assert pp.timeframe == "1h"
    assert pp.timeframe_ms == 60 * 60 * 1000
    assert pp.timeframe_s == 60 * 60
    assert pp.timeframe_m == 60


@enforce_types
def test_filter_feeds1():
    _test_filter_feeds("/")


@enforce_types
def test_filter_feeds2():
    _test_filter_feeds("-")


@enforce_types
def _test_filter_feeds(join_str):
    pp = mock_data_pp("5m", ["binance c ETH/USDT"])

    f1 = mock_feed("5m", "binance", f"BTC{join_str}USDT")
    f2 = mock_feed("5m", "binance", f"ETH{join_str}USDT")
    f3 = mock_feed("1h", "binance", f"BTC{join_str}USDT")
    cand_feeds = {f1.address: f1, f2.address: f2, f3.address: f3}

    final_feeds = pp.filter_feeds(cand_feeds)

    assert len(final_feeds) == 1
    assert list(final_feeds.keys()) == [f2.address]
    assert final_feeds[f2.address].name == f2.name
