from typing import Optional

from enforce_typing import enforce_types
import numpy as np
from sklearn.inspection import permutation_importance


class Aimodel:

    @enforce_types
    def __init__(
        self,
        scaler,
        sk_regrs: Optional[list],
        y_thr: Optional[float],
        sk_classif,
    ):
        self._scaler = scaler  # for scaling X-inputs
        self._sk_regrs = sk_regrs  # list of sklearn regressor model
        self._y_thr = y_thr  # threshold value for True vs False
        self._sk_classif = sk_classif  # sklearn classifier model
        self._imps_tup = None  # tuple of (imps_avg, imps_stddev)
        self._ycont_offset = 0.0  # offset to the output of regression

    @property
    def do_regr(self) -> bool:
        return self._sk_regrs is not None

    @enforce_types
    def predict_true(self, X):
        """
        @description
          Classify each input sample, with lower fidelity: just True vs False

        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          ytrue -- 1d array of [sample_i]:bool_value -- classifier model outputs
        """
        # We explicitly don't call sk_classif.predict() here, because it's
        #   inconsistent with predict_proba() for svc and maybe others.
        # Rather, draw on the probability output to guarantee consistency.
        yptrue = self.predict_ptrue(X)
        ytrue = yptrue > 0.5
        return ytrue

    @enforce_types
    def predict_ptrue(self, X: np.ndarray) -> np.ndarray:
        """
        @description
          Classify each input sample, with higher fidelity: prob of being True

        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          yptrue - 1d array of [sample_i]: prob_of_being_true -- model outputs
        """
        if self.do_regr:
            Ycont = self._predict_Ycont(X)
            assert self._y_thr is not None
            yptrue = np.mean(Ycont > self._y_thr, axis=1)
        else:
            X = self._scaler.transform(X)
            T = self._sk_classif.predict_proba(X)  # [sample_i][class_i]
            N = T.shape[0]
            class_i = 1  # this is the class for "True"
            yptrue = np.array([T[i, class_i] for i in range(N)])

        assert len(yptrue) == X.shape[0]
        return yptrue

    @enforce_types
    def predict_ycont(self, X):
        """
        @description
          Continuous-value prediction. For do_regr=True only.

        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          ycont -- 1d array of [sample_i]:cont_value -- regressor model outputs
        """
        assert self.do_regr
        Ycont = self._predict_Ycont(X)
        ycont = np.mean(Ycont, axis=1)
        assert len(ycont) == X.shape[0]
        return ycont

    @enforce_types
    def _predict_Ycont(self, X):
        """
        @description
          Continuous-value prediction. For do_regr=True only.

        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          Ycont -- 2d array of [sample_i, model_i]:cont_value -- regressor model outputs
        """
        assert self.do_regr
        N = X.shape[0]
        X_tr = self._scaler.transform(X)
        n_regrs = len(self._sk_regrs)
        Ycont = np.zeros((N, n_regrs), dtype=float)
        for i in range(n_regrs):
            Ycont[:, i] = self._sk_regrs[i].predict(X_tr) + self._ycont_offset
        return Ycont

    @enforce_types
    def set_ycont_offset(self, ycont_offset: float):
        self._ycont_offset = ycont_offset

    @enforce_types
    def importance_per_var(self, include_stddev: bool = False):
        """
        @description
          Report relative importance of each input variable

        @return
          imps_avg - 1d array of [var_i]: rel_importance_float
          (optional) imps_stddev -- array [var_i]: rel_stddev_float
        """
        assert self._imps_tup is not None
        if include_stddev:
            return self._imps_tup
        return self._imps_tup[0]

    @enforce_types
    def set_importance_per_var(self, X: np.ndarray, y: np.ndarray):
        """
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
          y -- 1d array of [sample_i]:value -- model outputs,
            where value is bool for classif (ytrue), or float for regr (ycont)

        @return
          <<sets self._imps_tup>>
        """
        assert not self._imps_tup, "have already set importances"
        self._imps_tup = self._calc_importance_per_var(X, y)

    @enforce_types
    def _calc_importance_per_var(self, X, y) -> tuple:
        """
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
          y -- 1d array of [sample_i]:value -- model outputs

        @return
          imps_avg -- 1d array of [var_i]: rel_importance_float
          imps_stddev -- array [var_i]: rel_stddev_float
        """
        n = X.shape[1]
        flat_imps_avg = np.ones(n, dtype=float) / n
        flat_imps_stddev = np.ones(n, dtype=float) / n

        is_constant = min(y) == max(y)
        if is_constant:
            return flat_imps_avg, flat_imps_stddev

        if self.do_regr:
            skm = self
            scoring = "neg_root_mean_squared_error"
        else:
            skm = self._sk_classif
            scoring = "f1"

        if self.do_regr:
            models = self._sk_regrs
        else:
            models = [self._sk_classif]

        if all(hasattr(model, 'coef_') for model in models):
            if self.do_regr:
                coefs = np.mean([np.abs(regr.coef_) for regr in self._sk_regrs], axis=0)
            else:
                coefs = np.abs(self._sk_classif.coef_)

            if len(coefs.shape) == 1:
                coefs = np.abs(coefs)
            else:
                coefs = np.mean(np.abs(coefs), axis=0)

            imps_avg = coefs / np.sum(coefs)
            imps_stddev = np.zeros_like(imps_avg)
        else:
            imps_bunch = permutation_importance(
                skm,
                X,
                y,
                scoring=scoring,
                n_repeats=30,  # magic number
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

    # for permutation_importance()
    def fit(self):
        return

    def predict(self, X):
        return self.predict_ycont(X)
