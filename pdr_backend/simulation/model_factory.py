from enforce_typing import enforce_types
from sklearn import linear_model, svm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF

from pdr_backend.simulation import prev_model
from pdr_backend.simulation.model_ss import ModelSS


@enforce_types
class ModelFactory:
    def __init__(self, model_ss: ModelSS):
        self.model_ss = model_ss

    def build(self, X_train, y_train):
        # print(f"Build model: start")
        model = self._model()
        model.fit(X_train, y_train)
        # print("Build model: done")
        return model

    def _model(self):
        a = self.model_ss.model_approach
        # print(f"model_approach={a}")
        if a == "PREV":
            return prev_model.PrevModel(self.model_ss.var_with_prev)
        if a == "LIN":
            return linear_model.LinearRegression()
        if a == "GPR":
            kernel = 1.0 * RBF(length_scale=1e1, length_scale_bounds=(1e-2, 1e3))
            return GaussianProcessRegressor(kernel=kernel, alpha=0.0)
        if a == "SVR":
            return svm.SVR()
        if a == "NuSVR":
            return svm.NuSVR()
        if a == "LinearSVR":
            return svm.LinearSVR()

        raise ValueError(a)
