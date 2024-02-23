from enforce_typing import enforce_types

@enforce_types
class Aimodel:
    """
    Acts like an sklearn model (skm),
    Plus has a less error-prone interface to get probabilities.
    """
    def __init__(self, skm):
        self._skm = skm

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

    def predict(self, *args, **kwargs):
        """
        @description
          Classify each input sample, with lower fidelity: just True vs False
        
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          ybool -- 1d array of [sample_i]:bool_value -- classifier model outputs
        """
        return self._skm.predict(*args, **kwargs)

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
        N = X.shape[1]
        yptrue = np.array([T[i,0] for i in range(N)])
        return yptrue
        
