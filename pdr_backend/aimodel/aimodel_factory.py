import copy

import numpy as np
from enforce_typing import enforce_types
from imblearn.over_sampling import SMOTE, RandomOverSampler  # type: ignore[import-untyped]
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
        ss = self.aimodel_ss
        n_True, n_False = sum(ybool), sum(np.invert(ybool))
        smallest_n = min(n_True, n_False)
        do_constant = (smallest_n == 0) or ss.approach == "Constant"

        # initialize skm (sklearn model)
        if do_constant:
            # force two classes in skm
            ybool = copy.copy(ybool)
            ybool[0], ybool[1] = True, False
            skm = DummyClassifier(strategy="most_frequent")
        elif ss.approach == "LinearLogistic":
            skm = LogisticRegression()
        elif ss.approach == "LinearSVC":
            skm = SVC(kernel="linear", probability=True, C=0.025)
        else:
            raise ValueError(ss.approach)

        # weight newest sample 10x, and 2nd-newest sample 5x
        # - assumes that newest sample is at index -1, and 2nd-newest at -2
        if do_constant:
            pass
        elif ss.weight_recent = "10x_5x":
            n_repeat1, xrecent1, yrecent1 = 10, X[-1, :], ybool[-1]
            n_repeat2, xrecent2, yrecent2 = 5, X[-2, :], ybool[-2]
            X = np.append(X, np.repeat(xrecent1[None], n_repeat1, axis=0), axis=0)
            X = np.append(X, np.repeat(xrecent2[None], n_repeat2, axis=0), axis=0)
            ybool = np.append(ybool, [yrecent1] * n_repeat1)
            ybool = np.append(ybool, [yrecent2] * n_repeat2)
        else:
            raise ValueError(ss.weight_recent)

        # balance data
        if do_constant or ss.balance_classes == "None":
            pass
        elif smallest_n <= 5 or ss.balance_classes == "RandomOverSampler":
            #  random oversampling for minority class
            X, ybool = RandomOverSampler().fit_resample(X, ybool)
        elif ss.balance_classes == "SMOTE":
            #  generate synthetic samples for minority class
            # (SMOTE = Synthetic Minority Oversampling Technique)
            X, y = SMOTE().fit_resample(X, ybool)
        else:
            raise ValueError(ss.balance)

        # scale inputs
        scaler = StandardScaler()
        scaler.fit(X)
        X = scaler.transform(X)

        # calibrate output probabilities
        if do_constant or ss.calibrate_probs == "None":
            pass
        elif ss.calibrate_probs == "CalibratedClassifierCV_5x":
            cv = min(smallest_n, 5)
            if cv > 1:
                skm = CalibratedClassifierCV(skm, cv=cv)
        else:
            raise ValueError(ss.calibrate_probs)    

        # fit model
        skm.fit(X, ybool)

        # calc variable importances
        if do_constant:
            imps = np.ones((X.shape[1],), dtype=float)
        else:
            imps_bunch = permutation_importance(skm, X, ybool, n_repeats=30)
            imps = imps_bunch["importances_mean"]
        imps = imps / sum(imps)  # normalize

        # return
        model = Aimodel(skm, scaler, imps)
        return model
