import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed, ArgFeeds
from pdr_backend.ppss.aimodel_ss import APPROACHES, AimodelSS


@enforce_types
def test_aimodel_ss_happy1():
    d = {
        "approach": "LIN",
        "max_n_train": 7,
        "autoregressive_n": 3,
        "input_feeds": ["kraken ETH/USDT hc", "binanceus ETH/USDT,TRX/DAI h"],
    }
    ss = AimodelSS(d)
    assert isinstance(ss.copy(), AimodelSS)

    # yaml properties
    assert ss.feeds_strs == ["kraken ETH/USDT hc", "binanceus ETH/USDT,TRX/DAI h"]
    assert ss.approach == "LIN"
    assert ss.max_n_train == 7
    assert ss.autoregressive_n == 3

    # derivative properties
    assert ss.feeds == ArgFeeds(
        [
            ArgFeed("kraken", "high", "ETH/USDT"),
            ArgFeed("kraken", "close", "ETH/USDT"),
            ArgFeed("binanceus", "high", "ETH/USDT"),
            ArgFeed("binanceus", "high", "TRX/DAI"),
        ]
    )

    # str
    assert "AimodelSS" in str(ss)
    assert "approach" in str(ss)


@enforce_types
def test_aimodel_ss_happy2():
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


@enforce_types
def test_aimodel_ss_unhappy1():
    d = {
        "approach": "LIN",
        "max_n_train": 7,
        "autoregressive_n": 3,
        "input_feeds": ["kraken ETH/USDT"],  # missing a signal like "c"
    }

    # it should complain that it's missing a signal in input feeds
    with pytest.raises(ValueError):
        AimodelSS(d)
