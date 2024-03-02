import copy

import numpy as np
from enforce_typing import enforce_types
from imblearn.over_sampling import SMOTE
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.inspection import permutation_importance
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
        do_constant = min(ybool) == max(ybool) or a == "Constant"
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

        # balance data: generate synthetic samples for minority class.
        # (SMOTE = Synthetic Minority Oversampling Technique)
        smote = SMOTE()
        X, ybool = smote.fit_resample(X, ybool)  

        # scale inputs
        scaler = StandardScaler()
        scaler.fit(X)
        X = scaler.transform(X)

        # calibrate output probabilities
        do_calibrate = (not do_constant)
        if do_calibrate:
            n_True, n_False = sum(ybool), sum(np.invert(ybool))
            smallest_n = min(n_True, n_False)
            cv = min(smallest_n, 5)
            if cv > 1:
                skm = CalibratedClassifierCV(skm, cv=cv)

        # fit model
        skm.fit(X, ybool)

        # calc variable importances
        imps_bunch = permutation_importance(skm, X, ybool, n_repeats=30)
        imps = imps_bunch["importances_mean"]
        imps = imps / sum(imps) # normalize

        # return
        model = Aimodel(skm, scaler, imps)
        return model
