from enforce_typing import enforce_types
from pdr_backend.cli.predict_feeds import PredictFeeds
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.util.currency_types import Eth


@enforce_types
def test_predictoor_ss():
    # build PredictoorSS
    d = predictoor_ss_test_dict()

    assert "feeds" in d
    d["feeds"] = [
        {
            "predict": "binance BTC/USDT c 5m",
            "train_on": "binance BTC/USDT c 5m",
        }
    ]

    assert "input_feeds" in d["aimodel_ss"]
    d["aimodel_ss"]["input_feeds"] = [
        "binance BTC/USDT c 5m",
        "kraken ETH/USDT o 1h",
    ]
    ss = PredictoorSS(d)

    # test yaml properties
    assert ss.feeds[0].predict == ArgFeed("binance", "close", "BTC/USDT", "5m")
    assert ss.aimodel_ss.feeds == [
        ArgFeed("binance", "close", "BTC/USDT", "5m"),
        ArgFeed("kraken", "open", "ETH/USDT", "1h"),
    ]

    assert ss.approach == 1
    assert ss.stake_amount == Eth(1)
    assert ss.others_stake == Eth(2313)
    assert ss.others_accuracy == pytest.approx(0.50001, abs=0.000001)
    assert ss.revenue.amt_eth == pytest.approx(0.93007, abs=0.000001)
    assert ss.s_until_epoch_end == 60

    # test str
    assert "PredictoorSS" in str(ss)

    # test setters
    ss.set_approach(2)
    assert ss.approach == 2


@enforce_types
def test_predictoor_ss_test_dict():
    # test - reasonable defaults when nothing passed in
    d = predictoor_ss_test_dict()
    f = d["feeds"]
    assert type(f) == list

    # test 5m
    predict_feeds = [
        {
            "predict": "binance ETH/USDT c 5m",
            "train_on": "binance ETH/USDT ADA/USDT c 5m",
        }
    ]
    d = predictoor_ss_test_dict(predict_feeds)
    assert d["feeds"] == predict_feeds
    assert d["aimodel_ss"]["input_feeds"] == [
        "binance ETH/USDT c 5m",
        "binance ADA/USDT c 5m",
    ]

    # test 1h
    predict_feeds = [
        {
            "predict": "binance ETH/USDT c 1h",
            "train_on": "binance ETH/USDT c 1h",
        }
    ]
    d = predictoor_ss_test_dict(predict_feeds)
    assert d["feeds"] == predict_feeds
    assert d["aimodel_ss"]["input_feeds"] == ["binance ETH/USDT c 1h"]

    # test s_start_payouts attribute set
    ss = PredictoorSS(d)

    assert ss.s_start_payouts == 0, "Must be unset in the test dict, so should return 0"

    # let's set it here
    d["bot_only"]["s_start_payouts"] = 100
    ss = PredictoorSS(d)
    assert ss.s_start_payouts == 100, "Must be set to 100"


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
