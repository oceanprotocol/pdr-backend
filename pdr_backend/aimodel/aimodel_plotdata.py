from typing import List

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.aimodel.aimodel import Aimodel

@enforce_types
class AimodelPlotdata:
    """Simple class to manage many inputs going into plot_model."""
    
    def __init__(
            self,
            model: Aimodel,
            X_train: np.ndarray,
            ytrue_train: np.ndarray,
            colnames: List[str],
            slicing_x: np.ndarray,
    ):
        """
        @arguments
          model -- Aimodel
          X_train -- 2d array [sample_i, var_i]:cont_value -- model trn inputs
          ytrue_train -- 1d array [sample_i]:bool_value -- model trn outputs
          colnames -- [var_i]:str -- name for each of the X inputs
          slicing_x -- arrat [dim_i]:floatval - when >2 dims, plot about this pt
        """
        # preconditions
        assert X_train.shape[1] == len(colnames) == slicing_x.shape[0], \
            (X_train.shape[1], len(colnames), slicing_x.shape[0])
        assert X_train.shape[0] == ytrue_train.shape[0], \
            (X_train.shape[0], ytrue_train.shape[0])

        # set values
        self.model = model
        self.X_train = X_train
        self.ytrue_train = ytrue_train
        self.colnames = colnames
        self.slicing_x = slicing_x
