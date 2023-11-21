from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.util.constants import CAND_TIMEFRAMES


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
    assert pp.predict_feed_tups == [("kraken", "high", "ETH-USDT")]
    assert pp.pair_strs == ["ETH-USDT"]
    assert pp.exchange_strs == ["kraken"]
    assert pp.predict_feed_tup == ("kraken", "high", "ETH-USDT")
    assert pp.exchange_str == "kraken"
    assert pp.signal_str == "high"
    assert pp.pair_str == "ETH-USDT"
    assert pp.base_str == "ETH"
    assert pp.quote_str == "USDT"

    # str
    assert "DataPP=" in str(pp)

    # setters
    pp.set_timeframe("1h")
    assert pp.timeframe == "1h"
    pp.set_predict_feeds(["binance oh BTC/DAI"])
    assert pp.predict_feeds_strs == ["binance oh BTC/DAI"]


@enforce_types
def test_data_pp_3feeds():
    pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["kraken h ETH/USDT", "binance oh BTC/USDT"],
            "sim_only": {"test_n": 2},
        }
    )

    # yaml properties
    assert pp.timeframe == "5m"
    assert pp.predict_feeds_strs == ["kraken h ETH/USDT", "binance oh BTC/USDT"]

    # derivative properties
    assert pp.predict_feed_tups == [
        ("kraken", "high", "ETH-USDT"),
        ("binance", "open", "BTC-USDT"),
        ("binance", "high", "BTC-USDT"),
    ]
    assert pp.pair_strs == ["ETH-USDT", "BTC-USDT"]
    assert pp.exchange_strs == ["kraken", "binance"]
    with pytest.raises(ValueError):
        pp.predict_feed_tup
    with pytest.raises(ValueError):
        pp.exchange_str
    with pytest.raises(ValueError):
        pp.signal_str
    with pytest.raises(ValueError):
        pp.pair_str
    with pytest.raises(ValueError):
        pp.base_str
    with pytest.raises(ValueError):
        pp.quote_str


@enforce_types
def test_data_pp_5m_vs_1h():
    # 5m
    pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["kraken h ETH/USDT"],
            "sim_only": {"test_n": 2},
        }
    )
    assert pp.timeframe == "5m"
    assert pp.timeframe_ms == 5 * 60 * 1000
    assert pp.timeframe_s == 5 * 60
    assert pp.timeframe_m == 5

    # 1h
    pp = DataPP(
        {
            "timeframe": "1h",
            "predict_feeds": ["kraken h ETH/USDT"],
            "sim_only": {"test_n": 2},
        }
    )
    assert pp.timeframe == "1h"
    assert pp.timeframe_ms == 60 * 60 * 1000
    assert pp.timeframe_s == 60 * 60
    assert pp.timeframe_m == 60
