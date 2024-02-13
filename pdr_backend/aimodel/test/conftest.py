import pytest
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_factory import RegressionModelFactory
from pdr_backend.ppss.aimodel_ss import RegressionModelSS


@enforce_types
@pytest.fixture()
def aimodel_factory():
    aimodel_ss = RegressionModelSS(
        {
            "approach": "LIN",
            "max_n_train": 7,
            "autoregressive_n": 3,
            "input_feeds": ["binance BTC/USDT c"],
        }
    )
    return RegressionModelFactory(aimodel_ss)
