import warnings
from unittest.mock import Mock

import numpy as np
from numpy.testing import assert_array_equal
import pytest
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.ppss.aimodel_ss import APPROACHES, AimodelSS

@enforce_types
def test_aimodel_factory_LinearLogistic():
    _test_aimodel_factory(approach="LinearLogistic")
    
@enforce_types
def test_aimodel_factory_LinearSVC():
    _test_aimodel_factory(approach="LinearSVC")

@enforce_types
def _test_aimodel_factory(approach):
    aimodel_ss = AimodelSS(
        {
            "approach": approach,
            "max_n_train": 7,
            "autoregressive_n": 3,
            "input_feeds": ["binance BTC/USDT c"],
        }
    )
    factory = AimodelFactory(aimodel_ss)
    assert isinstance(factory.aimodel_ss, AimodelSS)
    (X_train, ybool_train, X_test, ybool_test) = _data()

    # build
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # ignore ConvergenceWarning, more
        model = factory.build(X_train, ybool_train)

    # test predict_true()
    ybool_train_hat = model.predict_true(X_train)
    ybool_test_hat = model.predict_true(X_test)
    assert ybool_train_hat.dtype == bool
    assert ybool_test_hat.dtype == bool
    assert_array_equal(ybool_train, ybool_train_hat)
    assert_array_equal(ybool_test, ybool_test_hat)

    # test predict_ptrue()
    yptrue_train_hat = model.predict_ptrue(X_train)
    yptrue_test_hat = model.predict_ptrue(X_test)
    assert yptrue_train_hat.dtype == float
    assert yptrue_test_hat.dtype == float
    assert 0 < min(yptrue_train_hat) < max(yptrue_train_hat) < 1.0
    assert_array_equal(yptrue_train_hat > 0.5, ybool_train_hat)
    assert_array_equal(yptrue_test_hat > 0.5, ybool_test_hat)


@enforce_types
def _data() -> tuple:
    X_train = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
    ycont_train = f(X_train)
    y_thr = np.average(ycont_train)
    ybool_train = AimodelDataFactory.ycont_to_ybool(ycont_train, y_thr)

    X_test = np.array([[3, 5]])
    ycont_test = f(X_test)
    ybool_test = AimodelDataFactory.ycont_to_ybool(ycont_test, y_thr)

    return (X_train, ybool_train, X_test, ybool_test)


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
    ycont_train = np.array([5.3, 6.4, 7.5, 8.6, 9.7])  # oldest  # newest
    
    y_thr = 7.0
    ybool_train = AimodelDataFactory.ycont_to_ybool(ycont_train, y_thr)

    model = aimodel_factory.build(X_train, ybool_train)

    ybool_train_hat = model.predict_true(X_train)
    assert_array_equal(ybool_train, ybool_train_hat) # expect zero error

    yptrue_train_hat = model.predict_ptrue(X_train)
    assert_array_equal(yptrue_train_hat > 0.5, ybool_train_hat)


@enforce_types
def test_aimodel_factory_bad_approach():
    aimodel_ss = Mock(spec=AimodelSS)
    aimodel_ss.approach = "BAD"
    factory = AimodelFactory(aimodel_ss)

    X_train, ybool_train, _, _ = _data()

    # forcefully change the model
    with pytest.raises(ValueError):
        factory.build(X_train, ybool_train)
