from enforce_typing import enforce_types
import numpy as np


@enforce_types
class PrevModel:
    def __init__(self, var_with_prev: int):
        # which variable (= column in X) has the previous values
        # i.e. if we're predicting y[t], what column has y[y-1]
        self.var_with_prev = var_with_prev

    def fit(self, X_train, y_train):
        pass

    def predict(self, X) -> np.ndarray:
        return X[:, self.var_with_prev]
