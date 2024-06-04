import copy
import logging
from typing import Optional
import warnings

import numpy as np
from enforce_typing import enforce_types
from imblearn.over_sampling import SMOTE, RandomOverSampler  # type: ignore[import-untyped]
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import (
    ElasticNet,
    Lasso,
    LinearRegression,
    LogisticRegression,
    Ridge,
)
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.ppss.aimodel_ss import AimodelSS


logger = logging.getLogger("aimodel_factory")


@enforce_types
class AimodelFactory:
    def __init__(self, aimodel_ss: AimodelSS):
        self.ss = aimodel_ss

    def build(
        self,
        X: np.ndarray,
        ytrue: Optional[np.ndarray] = None,
        ycont: Optional[np.ndarray] = None,
        y_thr: Optional[float] = None,
        show_warnings: bool = True,
    ) -> Aimodel:
        """
        @description
          Train the model

        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
        
          ytrue -- 1d array of [sample_i]:bool_value -- classifier model outputs
          <or>
          ycont -- 1d array of [sample_i]:float_value -- regressor model outputs
          y_thr -- threshold value for True vs False

          show_warnings -- show warnings when building model?

        @return
          model -- Aimodel
        """
        do_regr = self.ss.do_regr
        assert all([not do_regr, have(ytrue), nothave(ycont), nothave(y_thr)])\
            or all([do_regr, nothave(ytrue), have(ycont), have(y_thr)]), \
            (do_regr, have(ytrue), have(ycont), have(y_thr))

        # regressor, wrapped by classifier
        if do_regr:
            return self._build_wrapped_regr(X, ycont, y_thr, show_warnings)

        # direct classifier
        return self._build_direct_classif(X, ytrue, show_warnings)

    def _build_wrapped_regr(
        self,
        X: np.ndarray,
        ycont: np.ndarray,
        y_thr: float,
        show_warnings: bool = True,
    ) -> Aimodel:
        assert self.ss.do_regr
        do_constant = min(ycont) == max(ycont)
        assert not do_constant, "FIXME handle constant build_wrapped_regr"

        ss = self.ss
        if ss.approach == "RegrLinearLS":
            sk_regr = LinearRegression()
        elif ss.approach == "RegrLinearLasso":
            sk_regr = Lasso()
        elif ss.approach == "RegrLinearRidge":
            sk_regr = Ridge()
        elif ss.approach == "RegrLinearElasticNet":
            sk_regr = ElasticNet()

        # error handling
        else:
            raise ValueError(ss.approach)

        # weight newest sample 10x, and 2nd-newest sample 5x
        # - assumes that newest sample is at index -1, and 2nd-newest at -2
        if do_constant or ss.weight_recent == "None":
            pass
        elif ss.weight_recent == "10x_5x":
            n_repeat1, n_repeat2 = 10, 5
            
            xrecent1, xrecent2 = X[-1, :], X[-2, :]
            X = np.append(X, np.repeat(xrecent1[None], n_repeat1, axis=0), axis=0)
            X = np.append(X, np.repeat(xrecent2[None], n_repeat2, axis=0), axis=0)

            yrecent1, yrecent2 = ycont[-1], ycont[-2]
            ycont = np.append(ycont, [yrecent1] * n_repeat1)
            ycont = np.append(ycont, [yrecent2] * n_repeat2)

        # balance data
        if ss.balance_classes != "None":
            logger.warning("In regression, non-None balance_classes is useless")
        
        # scale inputs
        scaler = StandardScaler()
        scaler.fit(X)
        X = scaler.transform(X)

        # in-place fit model
        # ideally: 5-10 models are built, using bootstrap sampling
        # FIXME: maybe use cross_val_predict()
        # https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.cross_val_predict.html#sklearn.model_selection.cross_val_predict
        _fit(sk_regr, X, ycont, show_warnings)
        sk_classif = FIXME

        # FIXME: maybe calibrate classifier
        if ss.calibrate_probs != "None":
            pass
                
        # calc variable importances
        imps_tup = self._calc_var_importances(do_constant, skm, X, ycont)

        # return
        model = Aimodel(scaler, sk_regr, sk_classif, imps_tup)
        return model


    # pylint: disable=too-many-statements
    def _build_direct_classif(
        self,
        X: np.ndarray,
        ytrue: np.ndarray,
        show_warnings: bool = True,
    ) -> Aimodel:
        assert not self.ss.do_regr
        ss = self.ss
        n_True, n_False = sum(ytrue), sum(np.invert(ytrue))
        smallest_n = min(n_True, n_False)
        do_constant = (smallest_n == 0) or ss.approach == "Constant"
        
        # initialize sk_classif (sklearn model)
        if do_constant:
            # force two classes in sk_classif
            ytrue = copy.copy(ytrue)
            ytrue[0], ytrue[1] = True, False
            sk_classif = DummyClassifier(strategy="most_frequent")

        # classifier approaches
        elif ss.approach == "LinearLogistic":
            sk_classif = LogisticRegression(max_iter=1000)
        elif ss.approach == "LinearLogistic_Balanced":
            sk_classif = LogisticRegression(max_iter=1000, class_weight="balanced")
        elif ss.approach == "LinearSVC":
            sk_classif = SVC(kernel="linear", probability=True, C=0.025)

        # error handling
        else:
            raise ValueError(ss.approach)

        # weight newest sample 10x, and 2nd-newest sample 5x
        # - assumes that newest sample is at index -1, and 2nd-newest at -2
        if do_constant or ss.weight_recent == "None":
            pass
        elif ss.weight_recent == "10x_5x":
            n_repeat1, n_repeat2 = 10, 5
            
            xrecent1, xrecent2 = X[-1, :], X[-2, :]
            X = np.append(X, np.repeat(xrecent1[None], n_repeat1, axis=0), axis=0)
            X = np.append(X, np.repeat(xrecent2[None], n_repeat2, axis=0), axis=0)
            yrecent1, yrecent2 = ytrue[-1], ytrue[-2]
            ytrue = np.append(ytrue, [yrecent1] * n_repeat1)
            ytrue = np.append(ytrue, [yrecent2] * n_repeat2)
        else:
            raise ValueError(ss.weight_recent)

        # scale inputs
        scaler = StandardScaler()
        scaler.fit(X)
        X = scaler.transform(X)

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

        # calibrate output probabilities
        if do_constant or ss.calibrate_probs == "None":
            pass
        elif ss.calibrate_probs in [
            "CalibratedClassifierCV_Sigmoid",
            "CalibratedClassifierCV_Isotonic",
        ]:
            N = X.shape[0]
            method = ss.calibrate_probs_skmethod(N)  # 'sigmoid' or 'isotonic'
            cv = min(smallest_n, 5)
            if cv > 1:
                sk_classif = CalibratedClassifierCV(
                    sk_classif,
                    method=method,
                    cv=cv,
                    ensemble=True,
                    n_jobs=-1,
                )
        else:
            raise ValueError(ss.calibrate_probs)

        # in-place fit model
        _fit(sk_classif, X, ytrue, show_warnings)
        
        # calc variable importances
        imps_tup = self._calc_var_importances(do_constant, sk_classif, X, ytrue)

        # return
        sk_regr = None
        model = Aimodel(scaler, sk_regr, sk_classif, imps_tup)
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

    
@enforce_types
def have(x) -> bool:
    return x is not None

@enforce_types
def nothave(x) -> bool:
    return x is None

@enforce_types
def _fit(skm, X, y, show_warnings:bool):
    """
    @description
      In-place fit a regressor or a classifier model

    @arguments
      skm -- sk_regr or sk_classif scikit-learn model
      X -- 2d array - model training inputs
      y -- ycont (if regr) or true (if classif) - model training outputs
      show_warnings -- show ConvergenceWarning etc?
    """
    if show_warnings:
        skm.fit(X, y)
        return
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        skm.fit(X, y)

        
