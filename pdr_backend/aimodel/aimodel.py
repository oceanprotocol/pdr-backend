from enforce_typing import enforce_types
import numpy as np


@enforce_types
class Aimodel:

    def __init__(self, skm, scaler):
        self._skm = skm  # sklearn model
        self._scaler = scaler

    def predict_true(self, X):
        """
        @description
          Classify each input sample, with lower fidelity: just True vs False

        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          ytrue -- 1d array of [sample_i]:bool_value -- classifier model outputs
        """
        # We explicitly don't call skm.predict() here, because it's
        #   inconsistent with predict_proba() for svc and maybe others.
        # Rather, draw on the probability output to guarantee consistency.
        yptrue = self.predict_ptrue(X)
        print(f"in predict_true(); yptrue[:10] = {yptrue[:10]}")
        ytrue = yptrue > 0.5
        return ytrue

    def predict_ptrue(self, X: np.ndarray) -> np.ndarray:
        """
        @description
          Classify each input sample, with higher fidelity: prob of being True

        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          yptrue - 1d array of [sample_i]: prob_of_being_true -- model outputs
        """
        X = self._scaler.transform(X)
        T = self._skm.predict_proba(X)  # [sample_i][class_i]
        N = T.shape[0]
        class_i = 1  # this is the class for "True"
        yptrue = np.array([T[i, class_i] for i in range(N)])
        return yptrue
