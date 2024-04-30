import copy
import warnings

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

    # pylint: disable=too-many-statements
    def build(
        self,
        X: np.ndarray,
        ytrue: np.ndarray,
        show_warnings: bool = True,
    ) -> Aimodel:
        """
        @description
          Train the model

        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
          ytrue -- 1d array of [sample_i]:bool_value -- classifier model outputs
          show_warnings -- show warnings when building model?

        @return
          model -- Aimodel
        """
        ss = self.aimodel_ss
        n_True, n_False = sum(ytrue), sum(np.invert(ytrue))
        smallest_n = min(n_True, n_False)
        do_constant = (smallest_n == 0) or ss.approach == "Constant"

        # initialize skm (sklearn model)
        if do_constant:
            # force two classes in skm
            ytrue = copy.copy(ytrue)
            ytrue[0], ytrue[1] = True, False
            skm = DummyClassifier(strategy="most_frequent")
        elif ss.approach == "LinearLogistic":
            skm = LogisticRegression()
        elif ss.approach == "LinearSVC":
            skm = SVC(kernel="linear", probability=True, C=0.025)
        else:
            raise ValueError(ss.approach)

        # weight newest sample 10x, and 2nd-newest sample 5x
        # - assumes that newest sample is at index -1, and 2nd-newest at -2
        if do_constant or ss.weight_recent == "None":
            pass
        elif ss.weight_recent == "10x_5x":
            n_repeat1, xrecent1, yrecent1 = 10, X[-1, :], ytrue[-1]
            n_repeat2, xrecent2, yrecent2 = 5, X[-2, :], ytrue[-2]
            X = np.append(X, np.repeat(xrecent1[None], n_repeat1, axis=0), axis=0)
            X = np.append(X, np.repeat(xrecent2[None], n_repeat2, axis=0), axis=0)
            ytrue = np.append(ytrue, [yrecent1] * n_repeat1)
            ytrue = np.append(ytrue, [yrecent2] * n_repeat2)
        else:
            raise ValueError(ss.weight_recent)

        # balance data
        if do_constant or ss.balance_classes == "None":
            pass
        elif smallest_n <= 5 or ss.balance_classes == "RandomOverSampler":
            #  random oversampling for minority class
            X, ytrue = RandomOverSampler().fit_resample(X, ytrue)
        elif ss.balance_classes == "SMOTE":
            #  generate synthetic samples for minority class
            # (SMOTE = Synthetic Minority Oversampling Technique)
            X, ytrue = SMOTE().fit_resample(X, ytrue)
        else:
            raise ValueError(ss.balance_classes)

        # scale inputs
        scaler = StandardScaler()
        scaler.fit(X)
        X = scaler.transform(X)

        # calibrate output probabilities
        if do_constant or ss.calibrate_probs == "None":
            pass
        elif ss.calibrate_probs == "CalibratedClassifierCV_5x":
            N = X.shape[0]
            method = "sigmoid" if N < 200 else "isotonic"
            cv = min(smallest_n, 5)
            if cv > 1:
                skm = CalibratedClassifierCV(
                    skm, method=method, cv=cv, ensemble=True, n_jobs=-1,
                )
        else:
            raise ValueError(ss.calibrate_probs)

        # fit model
        if show_warnings:  # show ConvergenceWarning, more
            skm.fit(X, ytrue)
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                skm.fit(X, ytrue)

        # calc variable importances
        imps_tup = self._calc_var_importances(do_constant, skm, X, ytrue)

        # return
        model = Aimodel(skm, scaler, imps_tup)
        return model

    def _calc_var_importances(self, do_constant: bool, skm, X, ytrue) -> tuple:
        """
        @return
          imps_avg - 1d array of [var_i]: rel_importance_float
          imps_stddev -- array [var_i]: rel_stddev_float
        """
        n = X.shape[1]
        flat_imps_avg = np.ones((n,), dtype=float) / n
        flat_imps_stddev = np.ones((n,), dtype=float) / n

        if do_constant:
            return flat_imps_avg, flat_imps_stddev

        imps_bunch = permutation_importance(
            skm,
            X,
            ytrue,
            n_repeats=30,
            scoring="accuracy",
        )
        imps_avg = imps_bunch.importances_mean

        if max(imps_avg) <= 0:  # all vars have negligible importance
            return flat_imps_avg, flat_imps_stddev

        imps_avg[imps_avg < 0.0] = 0.0  # some vars have negligible importance
        assert max(imps_avg) > 0.0, "should have some vars with imp > 0"

        imps_stddev = imps_bunch.importances_std

        # normalize
        _sum = sum(imps_avg)
        imps_avg = np.array(imps_avg) / _sum
        imps_stddev = np.array(imps_stddev) / _sum

        # postconditions
        assert imps_avg.shape == (n,)
        assert imps_stddev.shape == (n,)
        assert 1.0 - 1e-6 <= sum(imps_avg) <= 1.0 + 1e-6
        assert min(imps_avg) >= 0.0
        assert max(imps_avg) > 0
        assert min(imps_stddev) >= 0.0

        # return
        imps_tup = (imps_avg, imps_stddev)
        return imps_tup
