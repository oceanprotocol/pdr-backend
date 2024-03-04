import re

from enforce_typing import enforce_types
import numpy as np
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.aimodel_ss import (
    APPROACH_OPTIONS,
    WEIGHT_RECENT_OPTIONS,
    BALANCE_CLASSES_OPTIONS,
    CALIBRATE_PROBS_OPTIONS,
    AimodelSS,
    aimodel_ss_test_dict,
)


@enforce_types
def test_aimodel_ss_default_values():
    d = aimodel_ss_test_dict()
    ss = AimodelSS(d)

    assert ss.feeds_strs == ["binance BTC/USDT c"]
    assert ss.feeds == ArgFeeds([ArgFeed("binance", "close", "BTC/USDT")])

    assert ss.max_n_train == d["max_n_train"] == 7
    assert ss.autoregressive_n == d["autoregressive_n"] == 3

    assert ss.approach == d["approach"] == "LinearLogistic"
    assert ss.weight_recent == d["weight_recent"] == "10x_5x"
    assert ss.balance_classes == d["balance_classes"] == "SMOTE"
    assert ss.calibrate_probs == d["calibrate_probs"] == "CalibratedClassifierCV_5x"

    # str
    assert "AimodelSS" in str(ss)
    assert "approach" in str(ss)


@enforce_types
def test_aimodel_ss_nondefault_values():
    input_feeds = ["kraken ETH/USDT hc", "binance ETH/USDT TRX/DAI h"]
    d = aimodel_ss_test_dict(input_feeds=input_feeds)
    ss = AimodelSS(d)
    assert ss.feeds_strs == input_feeds
    assert ss.feeds == ArgFeeds(
        [
            ArgFeed("kraken", "high", "ETH/USDT"),
            ArgFeed("kraken", "close", "ETH/USDT"),
            ArgFeed("binance", "high", "ETH/USDT"),
            ArgFeed("binance", "high", "TRX/DAI"),
        ]
    )

    ss = AimodelSS(aimodel_ss_test_dict(max_n_train=39))
    assert ss.max_n_train == 39

    ss = AimodelSS(aimodel_ss_test_dict(autoregressive_n=13))
    assert ss.autoregressive_n == 13

    for approach in APPROACH_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(approach=approach))
        assert ss.approach == approach and approach in str(ss)

    for weight_recent in WEIGHT_RECENT_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(weight_recent=weight_recent))
        assert ss.weight_recent == weight_recent and weight_recent in str(ss)

    for balance_classes in BALANCE_CLASSES_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(balance_classes=balance_classes))
        assert ss.balance_classes == balance_classes and balance_classes in str(ss)

    for calibrate_probs in CALIBRATE_PROBS_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(calibrate_probs=calibrate_probs))
        assert ss.calibrate_probs == calibrate_probs and calibrate_probs in str(ss)


@enforce_types
def test_aimodel_ss_unhappy_inputs():
    input_feeds = ["kraken ETH/USDT"]  # missing eg "c"
    d = aimodel_ss_test_dict(input_feeds)
    with pytest.raises(
        AssertionError, match=re.escape("Missing attributes ['signal'] for some feeds")
    ):
        AimodelSS(d)

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(max_n_train=0))

    with pytest.raises(TypeError):
        AimodelSS(aimodel_ss_test_dict(max_n_train=3.1))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(autoregressive_n=0))

    with pytest.raises(TypeError):
        AimodelSS(aimodel_ss_test_dict(autoregressive_n=3.1))

    with pytest.raises(TypeError):
        AimodelSS(aimodel_ss_test_dict(autoregressive_n=np.inf))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(approach="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(weight_recent="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(balance_classes="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(calibrate_probs="foo"))
