import warnings

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.model_eng.model_factory import ModelFactory
from pdr_backend.model_eng.model_ss import APPROACHES, ModelSS


@enforce_types
def test_model_factory():
    for approach in APPROACHES:
        model_ss = ModelSS(approach)
        factory = ModelFactory(model_ss)
        assert isinstance(factory.model_ss, ModelSS)

        X, y, Xtest = _data()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # ignore ConvergenceWarning, more
            model = factory.build(X, y)

        ytest = model.predict(Xtest)
        assert len(ytest) == 1


def _data():
    X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])

    # y = 1 * x_0 + 2 * x_1 + 3
    y = np.dot(X, np.array([1, 2])) + 3

    Xtest = np.array([[3, 5]])

    return X, y, Xtest
