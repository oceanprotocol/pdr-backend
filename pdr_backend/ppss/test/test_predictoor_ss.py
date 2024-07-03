#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.util.currency_types import Eth


@enforce_types
def test_predictoor_ss_main():
    # build PredictoorSS
    d = predictoor_ss_test_dict()
    ss = PredictoorSS(d)

    # test yaml properties
    feedsets = ss.predict_train_feedsets
    assert len(feedsets) == 2
    f0, f1 = feedsets[0], feedsets[1]
    assert f0.predict == ArgFeed("binance", "close", "BTC/USDT", "5m")
    assert f0.train_on == [ArgFeed("binance", "close", "BTC/USDT", "5m")]
    assert f1.predict == ArgFeed("kraken", "close", "ETH/USDT", "5m")
    assert f1.train_on == [ArgFeed("kraken", "close", "ETH/USDT", "5m")]

    assert ss.approach == 1
    assert ss.stake_amount == Eth(1)
    assert ss.others_stake == Eth(2313)
    assert ss.others_accuracy == pytest.approx(0.50001, abs=0.000001)
    assert ss.revenue.amt_eth == pytest.approx(0.93007, abs=0.000001)
    assert ss.s_until_epoch_end == 60

    # test str
    assert "PredictoorSS" in str(ss)

    # test setters; test approach 2 & 3
    ss.set_approach(2)
    assert ss.approach == 2

    ss.set_approach(3)
    assert ss.approach == 3

    # test get_predict_train_feedset()
    assert ss.get_predict_train_feedset("binance", "BTC/USDT", "5m") == f0
    assert ss.get_predict_train_feedset("foo", "BTC/USDT", "5m") is None


@enforce_types
def test_predictoor_ss_feedsets_in_test_dict():
    # test 5m
    feedset_list = [
        {
            "predict": "binance ETH/USDT c 5m",
            "train_on": "binance ETH/USDT ADA/USDT c 5m",
        }
    ]
    d = predictoor_ss_test_dict(feedset_list)
    assert d["predict_train_feedsets"] == feedset_list

    # test 1h
    feedset_list = [
        {
            "predict": "binance ETH/USDT c 1h",
            "train_on": "binance ETH/USDT c 1h",
        }
    ]
    d = predictoor_ss_test_dict(feedset_list)
    assert d["predict_train_feedsets"] == feedset_list


@enforce_types
def test_predictoor_ss_start_payouts():
    # use defaults
    d = predictoor_ss_test_dict()
    ss = PredictoorSS(d)
    assert ss.s_start_payouts == 0

    # explicitly set
    d = predictoor_ss_test_dict()
    assert "bot_only" in d
    assert "s_start_payouts" in d["bot_only"]
    d["bot_only"]["s_start_payouts"] = 100
    ss = PredictoorSS(d)
    assert ss.s_start_payouts == 100


@enforce_types
def test_predictoor_ss_bad_approach():
    # catch bad approach in __init__()
    for bad_approach in [0, 4]:
        d = predictoor_ss_test_dict()
        assert "approach" in d
        d["approach"] = bad_approach
        with pytest.raises(ValueError):
            PredictoorSS(d)

    # catch bad approach in set_approach()
    for bad_approach in [0, 4]:
        d = predictoor_ss_test_dict()
        ss = PredictoorSS(d)
        with pytest.raises(ValueError):
            ss.set_approach(bad_approach)
