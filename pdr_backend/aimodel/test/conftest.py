import pytest
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.ppss.aimodel_ss import AimodelSS


@enforce_types
@pytest.fixture()
def aimodel_factory():
    aimodel_ss = AimodelSS(
        {
            "approach": "LinearLogistic",
            "max_n_train": 7,
            "autoregressive_n": 3,
            "input_feeds": ["binance BTC/USDT c"],
        }
    )
    return AimodelFactory(aimodel_ss)
