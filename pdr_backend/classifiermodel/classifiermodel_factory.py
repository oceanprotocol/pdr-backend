from enforce_typing import enforce_types
from sklearn import linear_model, svm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF

from pdr_backend.ppss.classifiermodel_ss import ClassifierModelSS


@enforce_types
class ClassifierModelFactory:
    def __init__(self, classifiermodel_ss: ClassifierModelSS):
        self.classifiermodel_ss = classifiermodel_ss

    def build(self, X_train, y_train):
        model = self._model()
        model.fit(X_train, y_train)
        return model

    def _model(self):
        a = self.classifiermodel_ss.approach
        return linear_model.LinearRegression()
