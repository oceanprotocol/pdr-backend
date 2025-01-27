from enforce_typing import enforce_types
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict


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

    # test str
    assert "PredictoorSS" in str(ss)

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
