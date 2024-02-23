from enforce_typing import enforce_types
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.ppss.aimodel_ss import AimodelSS

@enforce_types
class AimodelFactory:
    def __init__(self, aimodel_ss: AimodelSS):
        self.aimodel_ss = aimodel_ss

    def build(self, X: np.ndarray, ybool: np.ndarray) -> Aimodel:
        """
        @description
          Train the model
        
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
          ybool -- 1d array of [sample_i]:bool_value -- classifier model outputs

        @return
          model -- Aimodel
        """
        class_i, skm = self._model() #sklearn model
        model = Aimodel(class_i, skm)
        model.fit(X, ybool)
        return model

    def _model(self):
        a = self.aimodel_ss.approach
        if a == "LinearLogistic":
            return 1, LogisticRegression()
        if a == "LinearSVC":
            return 0, SVC(kernel="linear", probability=True, C=0.025)

        raise ValueError(a)

