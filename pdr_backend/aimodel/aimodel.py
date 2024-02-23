from enforce_typing import enforce_types
import numpy as np

@enforce_types
class Aimodel:
    """
    Acts like an sklearn model,
    Plus has a less error-prone interface to get probabilities.
    """
    def __init__(self, class_i, skm):
        self._class_i = class_i # class for predict_proba() for True values
        self._skm = skm # sklearn model

    def fit(self, *args, **kwargs):
        """
        @description
          Train the model
        
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
          ybool -- 1d array of [sample_i]:bool_value -- classifier model outputs

        @return
          (updates model in-place)
        """
        return self._skm.fit(*args, **kwargs)

    def predict_true(self, X):
        """
        @description
          Classify each input sample, with lower fidelity: just True vs False
        
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          ybool -- 1d array of [sample_i]:bool_value -- classifier model outputs
        """
        # We explicitly don't call skm.predict() here, because it's
        #   inconsistent with predict_proba() for svc and maybe others.
        # Rather, draw on the probability output to guarantee consistency.
        yptrue = self.predict_ptrue(X)
        return yptrue > 0.5

    def predict_ptrue(self, X: np.ndarray) -> np.ndarray:
        """
        @description
          Classify each input sample, with higher fidelity: prob of being True
        
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
        
        @return
          yptrue - 1d array of [sample_i]: prob_of_being_true -- model outputs
        """
        T = self._skm.predict_proba(X) # [sample_i][class_i]
        N = T.shape[0]
        yptrue = np.array([T[i,self._class_i] for i in range(N)])
        return yptrue
        
