from enforce_typing import enforce_types
import numpy as np


class Aimodel:

    @enforce_types
    def __init__(
        self,
        scaler,
        sk_regr,
        sk_classif,
        imps_tup: tuple,
    ):
        self._scaler = scaler  # for scaling X-inputs
        self._sk_regr = sk_regr # sklearn regressor model
        self._sk_classif = sk_classif  # sklearn classifier model
        self._imps_tup = imps_tup  # tuple of (imps_avg, imps_stddev)

    @property
    def do_regr(self) -> bool:
        return self._sk_regr is not None

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
            ycont = self.predict_ycont(X)
            raise NotImplementedError("build me")
        else:
            X = self._scaler.transform(X)
            T = self._sk_classif.predict_proba(X)  # [sample_i][class_i]
            N = T.shape[0]
            class_i = 1  # this is the class for "True"
            yptrue = np.array([T[i, class_i] for i in range(N)])
            
        return yptrue

    @enforce_types
    def importance_per_var(self, include_stddev: bool = False):
        """
        @description
          Report relative importance of each input variable

        @return
          imps_avg - 1d array of [var_i]: rel_importance_float
          (optional) imps_stddev -- array [var_i]: rel_stddev_float
        """
        if include_stddev:
            return self._imps_tup
        return self._imps_tup[0]

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
        ycont = self._sk_regr.predict(X)
        return ycont
