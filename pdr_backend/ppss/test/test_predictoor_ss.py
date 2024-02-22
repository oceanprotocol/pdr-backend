from enforce_typing import enforce_types

from pdr_backend.ppss.predictoor_ss import PredictoorSS


@enforce_types
def test_predictoor_ss():
    d = {
        "predict_feed": "binance BTC/USDT c 5m",
        "stake_amount": 1,
        "sim_only": {
            "weekly_revenue_amount": 1875,
            "others_stake_amount": 2313,
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
    assert ss.weekly_revenue_amount == 1875
    assert ss.others_stake_amount == 2313
    assert ss.s_until_epoch_end == 60

    # str
    assert "PredictoorSS" in str(ss)
