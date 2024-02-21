import warnings
from unittest.mock import Mock

import numpy as np
import pytest
from enforce_typing import enforce_types

from pdr_backend.regressionmodel.regressionmodel_factory import RegressionModelFactory
from pdr_backend.ppss.regressionmodel_ss import APPROACHES, RegressionModelSS


@enforce_types
def test_aimodel_factory_basic():
    for approach in APPROACHES:
        regressionmodel_ss = RegressionModelSS(
            {
                "approach": approach,
                "max_n_train": 7,
                "autoregressive_n": 3,
                "input_feeds": ["binance BTC/USDT c"],
            }
        )
        factory = RegressionModelFactory(regressionmodel_ss)
        assert isinstance(factory.regressionmodel_ss, RegressionModelSS)

        (X_train, y_train, X_test, y_test) = _data()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # ignore ConvergenceWarning, more
            model = factory.build(X_train, y_train)

        y_test_hat = model.predict(X_test)
        assert y_test_hat.shape == y_test.shape


@enforce_types
def test_aimodel_accuracy_from_xy(aimodel_factory):
    (X_train, y_train, X_test, y_test) = _data()

    aimodel = aimodel_factory.build(X_train, y_train)

    y_train_hat = aimodel.predict(X_train)
    assert sum(abs(y_train - y_train_hat)) < 1e-10  # near-perfect since linear

    y_test_hat = aimodel.predict(X_test)
    assert sum(abs(y_test - y_test_hat)) < 1e-10


@enforce_types
def _data() -> tuple:
    X_train = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
    y_train = f(X_train)

    X_test = np.array([[3, 5]])
    y_test = f(X_test)

    return (X_train, y_train, X_test, y_test)


@enforce_types
def f(X: np.ndarray) -> np.ndarray:
    # y = 3 * x0 + 2 * x1
    y = 3.0 + 1.0 * X[:, 0] + 2.0 * X[:, 1]
    return y


@enforce_types
def test_aimodel_accuracy_from_create_xy(aimodel_factory):
    # This is from a test function in test_model_data_factory.py

    # The underlying AR process is: close[t] = close[t-1] + open[t-1]
    X_train = np.array(
        [
            [0.1, 0.1, 3.1, 4.2],  # oldest
            [0.1, 0.1, 4.2, 5.3],
            [0.1, 0.1, 5.3, 6.4],
            [0.1, 0.1, 6.4, 7.5],
            [0.1, 0.1, 7.5, 8.6],
        ]
    )  # newest
    y_train = np.array([5.3, 6.4, 7.5, 8.6, 9.7])  # oldest  # newest

    aimodel = aimodel_factory.build(X_train, y_train)

    y_train_hat = aimodel.predict(X_train)
    assert sum(abs(y_train - y_train_hat)) < 1e-10  # near-perfect since linear


@enforce_types
def test_aimodel_factory_bad_approach():
    regressionmodel_ss = Mock(spec=RegressionModelSS)
    regressionmodel_ss.approach = "BAD"
    factory = RegressionModelFactory(regressionmodel_ss)

    X_train, y_train, _, _ = _data()

    # forcefully change the model
    with pytest.raises(ValueError):
        factory.build(X_train, y_train)
