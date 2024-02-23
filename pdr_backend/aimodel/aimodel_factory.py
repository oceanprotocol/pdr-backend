from enforce_typing import enforce_types
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from pdr_backend.ppss.aimodel_ss import AimodelSS


@enforce_types
class AimodelFactory:
    def __init__(self, aimodel_ss: AimodelSS):
        self.aimodel_ss = aimodel_ss

    def build(self, X_train, y_train):
        model = self._model()
        model.fit(X_train, y_train)
        return model

    def _model(self):
        a = self.aimodel_ss.approach
        if a == "LinearLogistic":
            return LogisticRegression()
        if a == "LinearSVC":
            return SVC(kernel="linear", C=0.025, random_state=42)

        raise ValueError(a)
