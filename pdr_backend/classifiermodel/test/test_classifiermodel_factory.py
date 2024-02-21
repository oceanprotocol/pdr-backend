import warnings

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.classifiermodel.classifiermodel_factory import ClassifierModelFactory
from pdr_backend.ppss.classifiermodel_ss import APPROACHES, ClassifierModelSS


@enforce_types
def test_classifiermodel_factory_basic():
    for approach in APPROACHES:
        classifiermodel_ss = ClassifierModelSS(
            {
                "approach": approach,
                "max_n_train": 7,
                "autoregressive_n": 3,
                "input_feeds": ["binance BTC/USDT c"],
            }
        )
        factory = ClassifierModelFactory(classifiermodel_ss)
        assert isinstance(factory.classifiermodel_ss, ClassifierModelSS)

        (X_train, y_train, X_test, y_test) = _data()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # ignore ConvergenceWarning, more
            model = factory.build(X_train, y_train)

        y_test_hat = model.predict(X_test)
        assert y_test_hat.shape == y_test.shape


@enforce_types
def test_classifiermodel_accuracy_from_xy(classifiermodel_factory):
    (X_train, y_train, X_test, y_test) = _data()

    classifiermodel = classifiermodel_factory.build(X_train, y_train)

    y_train_hat = classifiermodel.predict(X_train)
    assert sum(abs(y_train - y_train_hat)) == 0

    y_test_hat = classifiermodel.predict(X_test)
    assert sum(abs(y_test - y_test_hat)) == 0


@enforce_types
def _data() -> tuple:
    X_train = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
    y_train = f(X_train)

    X_test = np.array([[3, 5]])
    y_test = f(X_test)

    return (X_train, y_train, X_test, y_test)


@enforce_types
def f(X: np.ndarray) -> np.ndarray:
    y = (X[:, 1] > X[:, 0]).astype(int)
    return y


@enforce_types
def test_classifiermodel_accuracy_from_create_xy(classifiermodel_factory):
    # This is from a test function in test_model_data_factory.py

    # The underlying AR process is: close[t] = close[t-1] + open[t-1]
    X_train = np.array(
        [
            [0.2, 0.2, 3.1, 4.2],  # oldest
            [0.1, 0.1, 4.2, 5.3],
            [0.2, 0.2, 5.3, 6.4],
            [0.1, 0.1, 6.4, 7.5],
            [0.2, 0.2, 7.5, 8.6],
        ]
    )  # newest
    y_train = np.array([1, 0, 1, 0, 1])  # oldest  # newest
    X_train = classifiermodel_factory.scale_train_data(X_train)
    classifiermodel = classifiermodel_factory.build(X_train, y_train)

    y_train_hat = classifiermodel.predict(X_train)
    print(y_train_hat, y_train)
    assert sum(abs(y_train - y_train_hat)) == 0  # exactly same
