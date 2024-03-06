from enforce_typing import enforce_types
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict


@enforce_types
def test_predictoor_ss():
    # build PredictoorSS
    d = predictoor_ss_test_dict()

    assert "predict_feed" in d
    d["predict_feed"] = "binance BTC/USDT c 5m"

    assert "input_feeds" in d["aimodel_ss"]
    d["aimodel_ss"]["input_feeds"] = [
        "binance BTC/USDT c 5m",
        "kraken ETH/USDT o 1h",
    ]
    ss = PredictoorSS(d)

    # test yaml properties
    assert ss.feed == ArgFeed("binance", "close", "BTC/USDT", "5m")
    assert ss.aimodel_ss.feeds == [
        ArgFeed("binance", "close", "BTC/USDT", "5m"),
        ArgFeed("kraken", "open", "ETH/USDT", "1h"),
    ]

    assert ss.approach == 1
    assert ss.stake_amount == 1
    assert ss.others_stake == 2313
    assert ss.others_accuracy == pytest.approx(0.50001, abs=0.000001)
    assert ss.revenue == pytest.approx(0.93007, abs=0.000001)
    assert ss.s_until_epoch_end == 60

    # test str
    assert "PredictoorSS" in str(ss)

    # test setters
    ss.set_approach(2)
    assert ss.approach == 2


@enforce_types
def test_predictoor_ss_test_dict():
    # test - reasoonable defaults when nothing passed in
    d = predictoor_ss_test_dict()
    f = d["predict_feed"]
    assert "binance" in f or "kraken" in f
    assert "BTC" in f or "ETH" in f
    assert "5m" in f or "1h" in f
    assert d["aimodel_ss"]["input_feeds"] == [f]

    # test 5m
    d = predictoor_ss_test_dict("binance ETH/USDT c 5m")
    assert d["predict_feed"] == "binance ETH/USDT c 5m"
    assert d["aimodel_ss"]["input_feeds"] == ["binance ETH/USDT c 5m"]

    # test 1h
    d = predictoor_ss_test_dict("binance ETH/USDT c 1h")
    assert d["predict_feed"] == "binance ETH/USDT c 1h"
    assert d["aimodel_ss"]["input_feeds"] == ["binance ETH/USDT c 1h"]


@enforce_types
def test_predictoor_ss_bad_approach():
    # catch bad approach in __init__()
    for bad_approach in [0, 3]:
        d = predictoor_ss_test_dict()
        d["approach"] = bad_approach
        with pytest.raises(ValueError):
            PredictoorSS(d)

    # catch bad approach in set_approach()
    for bad_approach in [0, 3]:
        d = predictoor_ss_test_dict()
        ss = PredictoorSS(d)
        with pytest.raises(ValueError):
            ss.set_approach(bad_approach)
