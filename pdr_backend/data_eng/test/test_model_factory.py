import warnings

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.data_eng.model_factory import ModelFactory
from pdr_backend.ppss.model_ss import APPROACHES, ModelSS


@enforce_types
def test_model_factory_basic():
    for approach in APPROACHES:
        model_ss = ModelSS({"approach": approach})
        factory = ModelFactory(model_ss)
        assert isinstance(factory.model_ss, ModelSS)

        (X_train, y_train, X_test, y_test) = _data()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # ignore ConvergenceWarning, more
            model = factory.build(X_train, y_train)

        y_test_hat = model.predict(X_test)
        assert y_test_hat.shape == y_test.shape


@enforce_types
def test_model_factory_accuracy():
    model_ss = ModelSS({"approach": "LIN"})
    factory = ModelFactory(model_ss)

    (X_train, y_train, X_test, y_test) = _data()

    model = factory.build(X_train, y_train)
    
    y_train_hat = model.predict(X_train)
    assert sum(abs(y_train - y_train_hat)) < 1e-10 # near-perfect since linear

    y_test_hat = model.predict(X_test)
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
    y = 3.0 + 1.0 * X[:,0] + 2.0 * X[:,1]
    return y
