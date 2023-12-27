from enforce_typing import enforce_types

from pdr_backend.ppss.predictoor_ss import PredictoorSS


@enforce_types
def test_predictoor_ss():
    d = {
        "predict_feed": "binance BTC/USDT c",
        "timeframe": "5m",
        "bot_only": {
            "s_until_epoch_end": 60,
            "stake_amount": 1,
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
    assert ss.s_until_epoch_end == 60
    assert ss.stake_amount == 1

    # str
    assert "PredictoorSS" in str(ss)
