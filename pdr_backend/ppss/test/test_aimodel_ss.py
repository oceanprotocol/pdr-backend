import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.aimodel_ss import APPROACHES, AimodelSS


@enforce_types
def test_aimodel_ss1():
    # TODO: more after splitting the data ss tests
    d = {
        "approach": "LIN",
        "max_n_train": 7,
        "autoregressive_n": 3,
        "input_feeds": ["binance BTC/USDT c"],
    }
    ss = AimodelSS(d)

    # yaml properties
    assert ss.approach == "LIN"

    # str
    assert "AimodelSS" in str(ss)
    assert "approach" in str(ss)


@enforce_types
def test_aimodel_ss2():
    for approach in APPROACHES:
        ss = AimodelSS(
            {
                "approach": approach,
                "max_n_train": 7,
                "autoregressive_n": 3,
                "input_feeds": ["binance BTC/USDT c"],
            }
        )
        assert approach in str(ss)

    with pytest.raises(ValueError):
        AimodelSS(
            {
                "approach": "foo_approach",
                "max_n_train": 7,
                "autoregressive_n": 3,
                "input_feeds": ["binance BTC/USDT c"],
            }
        )
