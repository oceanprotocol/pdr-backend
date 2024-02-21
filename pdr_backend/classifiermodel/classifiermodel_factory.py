from enforce_typing import enforce_types
from sklearn import linear_model
from sklearn.preprocessing import StandardScaler

from pdr_backend.ppss.classifiermodel_ss import ClassifierModelSS


@enforce_types
class ClassifierModelFactory:
    def __init__(self, classifiermodel_ss: ClassifierModelSS):
        self.classifiermodel_ss = classifiermodel_ss
        self.scaler = StandardScaler()

    def scale_train_data(self, X_train):
        return self.scaler.fit_transform(X_train)

    def build(self, X_train, y_train):
        model = self._model()
        model.fit(X_train, y_train)
        return model

    def _model(self):
        return linear_model.LogisticRegression()
