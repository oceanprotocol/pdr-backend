import copy
import logging
from typing import Optional
import warnings

import numpy as np
from enforce_typing import enforce_types
from imblearn.over_sampling import SMOTE, RandomOverSampler  # type: ignore[import-untyped]
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.gaussian_process import (
    GaussianProcessClassifier,
    GaussianProcessRegressor,
)
from sklearn.linear_model import (
    ElasticNet,
    Lasso,
    LinearRegression,
    LogisticRegression,
    Ridge,
)
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier, XGBRegressor

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
        # regressor, wrapped by classifier
        if self.ss.do_regr:
            return self._build_wrapped_regr(X, ycont, y_thr, show_warnings)  # type: ignore

        # direct classifier
        return self._build_direct_classif(X, ytrue, show_warnings)  # type: ignore

    def _build_wrapped_regr(
        self,
        X: np.ndarray,
        ycont: np.ndarray,
        y_thr: float,
        show_warnings: bool = True,
    ) -> Aimodel:
        ss = self.ss
        assert ss.do_regr
        assert ycont is not None
        assert X.shape[0] == ycont.shape[0], (X.shape[0], ycont.shape[0])
        do_constant = min(ycont) == max(ycont) or ss.approach == "RegrConstant"

        # weight newest sample 10x, and 2nd-newest sample 5x
        # - assumes that newest sample is at index -1, and 2nd-newest at -2
        n_repeat1, n_repeat2 = ss.weight_recent_n
        if do_constant or n_repeat1 == 0:
            pass
        else:
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
        X_tr = scaler.transform(X)

        # in-place fit model
        if do_constant:
            sk_regr = DummyRegressor(strategy="constant", constant=ycont[0])
            _fit(sk_regr, X_tr, ycont, show_warnings)
            sk_regrs = [sk_regr]
        else:
            sk_regrs = []
            n_regrs = 10  # magic number
            for _ in range(n_regrs):
                N = len(ycont)
                I = np.random.choice(a=N, size=N, replace=True)
                X_tr_I, ycont_I = X_tr[I, :], ycont[I]
                sk_regr = _approach_to_skm(ss.approach)
                _fit(sk_regr, X_tr_I, ycont_I, show_warnings)
                sk_regrs.append(sk_regr)

        # model
        model = Aimodel(scaler, sk_regrs, y_thr, None)

        if ss.calibrate_regr == "CurrentYval":
            current_yval = ycont[-1]
            current_yvalhat = model.predict_ycont(X)[-1]
            ycont_offset = current_yval - current_yvalhat
            model.set_ycont_offset(ycont_offset)

        # variable importances
        if self.ss.calc_imps:
            model.set_importance_per_var(X, ycont)

        # return
        return model

    # pylint: disable=too-many-statements
    def _build_direct_classif(
        self,
        X: np.ndarray,
        ytrue: np.ndarray,
        show_warnings: bool = True,
    ) -> Aimodel:
        ss = self.ss
        assert not ss.do_regr
        assert X.shape[0] == len(ytrue), (X.shape[0], len(ytrue))
        n_True, n_False = sum(ytrue), sum(np.invert(ytrue))
        smallest_n = min(n_True, n_False)
        do_constant = (smallest_n == 0) or ss.approach == "ClassifConstant"

        # initialize sk_classif (sklearn model)
        if do_constant:
            # force two classes in sk_classif
            ytrue = copy.copy(ytrue)
            ytrue[0], ytrue[1] = True, False
            sk_classif = DummyClassifier(strategy="most_frequent")
        else:
            sk_classif = _approach_to_skm(ss.approach)
        if sk_classif is None:
            raise ValueError(ss.approach)

        # weight newest sample 10x, and 2nd-newest sample 5x
        # - assumes that newest sample is at index -1, and 2nd-newest at -2
        n_repeat1, n_repeat2 = ss.weight_recent_n
        if do_constant or n_repeat1 == 0:
            pass
        else:
            xrecent1, xrecent2 = X[-1, :], X[-2, :]
            X = np.append(X, np.repeat(xrecent1[None], n_repeat1, axis=0), axis=0)
            X = np.append(X, np.repeat(xrecent2[None], n_repeat2, axis=0), axis=0)
            yrecent1, yrecent2 = ytrue[-1], ytrue[-2]
            ytrue = np.append(ytrue, [yrecent1] * n_repeat1)
            ytrue = np.append(ytrue, [yrecent2] * n_repeat2)

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
            cv = 5  # number of cv folds. magic number
            cv = min(smallest_n, cv)
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

        # model
        model = Aimodel(scaler, None, None, sk_classif)

        # variable importances
        if self.ss.calc_imps:
            model.set_importance_per_var(X, ytrue)

        # return
        return model


@enforce_types
def _fit(skm, X, y, show_warnings: bool):
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


@enforce_types
def _approach_to_skm(approach: str):
    # pylint: disable=too-many-return-statements
    if approach in ["ClassifConstant", "RegrConstant"]:
        raise ValueError("should have handled constants before this")

    # regressor approaches
    if approach == "RegrLinearLS":
        return LinearRegression()
    if approach == "RegrLinearLasso":
        return Lasso()
    if approach == "RegrLinearRidge":
        return Ridge()
    if approach == "RegrLinearElasticNet":
        return ElasticNet()
    if approach == "RegrGaussianProcess":
        return GaussianProcessRegressor()
    if approach == "RegrXgboost":
        return XGBRegressor()

    # classifier approaches
    if approach == "ClassifLinearLasso":
        return LogisticRegression(penalty="l1", solver="liblinear", max_iter=1000)
    if approach == "ClassifLinearLasso_Balanced":
        return LogisticRegression(
            penalty="l1", solver="liblinear", max_iter=1000, class_weight="balanced"
        )
    if approach == "ClassifLinearRidge":
        return LogisticRegression(penalty="l2", solver="lbfgs", max_iter=1000)
    if approach == "ClassifLinearRidge_Balanced":
        return LogisticRegression(
            penalty="l2", solver="lbfgs", max_iter=1000, class_weight="balanced"
        )
    if approach == "ClassifLinearElasticNet":
        return LogisticRegression(
            penalty="elasticnet", l1_ratio=0.5, solver="saga", max_iter=1000
        )
    if approach == "ClassifLinearElasticNet_Balanced":
        return LogisticRegression(
            penalty="elasticnet",
            l1_ratio=0.5,
            solver="saga",
            max_iter=1000,
            class_weight="balanced",
        )
    if approach == "ClassifLinearSVM":
        return SVC(kernel="linear", probability=True, C=0.025)
    if approach == "ClassifGaussianProcess":
        return GaussianProcessClassifier()
    if approach == "ClassifXgboost":
        return XGBClassifier()

    # unidentified
    return None
