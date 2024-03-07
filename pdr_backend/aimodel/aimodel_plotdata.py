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
    ):
        """
        @arguments
          model -- Aimodel
          X_train -- 2d array [sample_i, var_i]:cont_value -- model trn inputs
          ytrue_train -- 1d array [sample_i]:bool_value -- model trn outputs
          colnames -- [var_i]:str -- name for each of the X inputs
        """
        self.model = model
        self.X_train = X_train
        self.ytrue_train = ytrue_train
        self.colnames = colnames
