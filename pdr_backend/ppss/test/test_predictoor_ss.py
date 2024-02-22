from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.predictoor_ss import PredictoorSS


@enforce_types
def test_predictoor_ss():
    d = {
        "predict_feed": "binance BTC/USDT c 5m",
        "stake_amount": 1,
        "sim_only": {
            "others_stake": 2313,
            "others_accuracy": 0.50001,
            "revenue": 0.93007,
        },
        "bot_only": {
            "s_until_epoch_end": 60,
        },
        "aimodel_ss": {
            "input_feeds": ["binance BTC/USDT c"],
            "approach": "LIN",
            "max_n_train": 7,
            "autoregressive_n": 3,
        },
    }
    ss = PredictoorSS(d)

    # yaml properties
    assert ss.stake_amount == 1
    assert ss.others_stake == 2313
    assert ss.others_accuracy == pytest.approx(0.50001, abs=0.000001)
    assert ss.revenue == pytest.approx(0.93007, abs=0.000001)
    assert ss.s_until_epoch_end == 60

    # str
    assert "PredictoorSS" in str(ss)
