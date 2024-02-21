import pytest
from enforce_typing import enforce_types

from pdr_backend.classifiermodel.classifiermodel_factory import ClassifierModelFactory
from pdr_backend.ppss.classifiermodel_ss import ClassifierModelSS


@enforce_types
@pytest.fixture()
def classifiermodel_factory():
    classifiermodel_ss = ClassifierModelSS(
        {
            "approach": "LIN",
            "max_n_train": 7,
            "autoregressive_n": 3,
            "input_feeds": ["binance BTC/USDT c"],
        }
    )
    return ClassifierModelFactory(classifiermodel_ss)
