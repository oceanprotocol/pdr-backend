from enforce_typing import enforce_types
from sklearn import linear_model, svm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF

from pdr_backend.ppss.regressionmodel_ss import RegressionModelSS


@enforce_types
class ModelFactoryBase:
    def __init__(self, regressionmodel_ss: RegressionModelSS):
        self.regressionmodel_ss = regressionmodel_ss

    def build(self, X_train, y_train):
        model = self._model()
        model.fit(X_train, y_train)
        return model

    def _model(self):
        a = self.regressionmodel_ss.approach
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
