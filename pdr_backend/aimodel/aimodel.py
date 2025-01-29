from typing import Optional

from enforce_typing import enforce_types
import numpy as np


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
            if hasattr(self._sk_classif, "_predict_proba_lr"):
                T = self._sk_classif._predict_proba_lr(X)  # required for LinearSVC()
            else:
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

    def predict(self, X):
        return self.predict_ycont(X)
