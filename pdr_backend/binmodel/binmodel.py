from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.binmodel.constants import UP, DOWN


@enforce_types
class Binmodel(dict):

    def __init__(self, model_UP: Aimodel, model_DOWN: Aimodel):
        self[UP] = model_UP
        self[DOWN] = model_DOWN

    def predict_next(self, X_test: dict) -> dict:
        """
        @arguments
          X_test_dict -- dict of {UP: X_test_UP_array, DOWN: X_test_DOWN_arr.}
            It expects each array to have exactly 1 row, to predict from

        @return
          predprob -- dict of {UP: predprob_UP_float, DOWN: predprob_DOWN_float}
        """
        assert X_test[UP].shape[0] == 1
        assert X_test[DOWN].shape[0] == 1

        prob_UP = self[UP].predict_ptrue(X_test[UP])[0]
        prob_DOWN = self[DOWN].predict_ptrue(X_test[UP])[0]

        # ensure not np.float64. Why: applying ">" gives np.bool --> problems
        prob_UP, prob_DOWN = float(prob_UP), float(prob_DOWN)

        return {UP: prob_UP, DOWN: prob_DOWN}
