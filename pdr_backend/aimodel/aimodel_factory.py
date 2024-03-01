import copy

import numpy as np
from enforce_typing import enforce_types
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
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
        a = self.aimodel_ss.approach
        do_constant = (min(ybool) == max(ybool) or a == "Constant")
        if do_constant:
            # force two classes in skm
            ybool = copy.copy(ybool)
            ybool[0] = True
            ybool[1] = False
            skm = DummyClassifier(strategy="most_frequent")
        elif a == "LinearLogistic":
            skm = LogisticRegression()
        elif a == "LinearSVC":
            skm = SVC(kernel="linear", probability=True, C=0.025)
        else:
            raise ValueError(a)

        scaler = StandardScaler()
        scaler.fit(X)

        X = scaler.transform(X)

        if not do_constant:
            n_True, n_False = sum(ybool), sum(np.invert(ybool))
            smallest_n = min(n_True, n_False)
            cv = min(smallest_n, 5)
            if cv > 1:
                skm = CalibratedClassifierCV(skm, cv=cv)

        skm.fit(X, ybool)

        model = Aimodel(skm, scaler)
        return model
