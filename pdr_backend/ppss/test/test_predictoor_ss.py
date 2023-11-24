from enforce_typing import enforce_types

from pdr_backend.ppss.predictoor_ss import PredictoorSS


@enforce_types
def test_predictoor_ss():
    d = {
        "bot_only": {
            "s_until_epoch_end": 60,
            "stake_amount": 1,
        }
    }
    ss = PredictoorSS(d)

    # yaml properties
    assert ss.s_until_epoch_end == 60
    assert ss.stake_amount == 1

    # str
    assert "PredictoorSS" in str(ss)
