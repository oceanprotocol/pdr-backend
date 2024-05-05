from typing import List, Optional

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.aimodel.aimodel import Aimodel


class AimodelPlotdata:
    """Simple class to manage many inputs going into plot_model."""

    def __init__(
        self,
        model: Aimodel,
        X_train: np.ndarray,
        ytrue_train: np.ndarray,
        colnames: List[str],
        slicing_x: np.ndarray,
        sweep_vars: Optional[List[int]] = None,
    ):
        """
        @arguments
          model -- Aimodel
          X_train -- 2d array [sample_i, var_i]:cont_value -- model trn inputs
          ytrue_train -- 1d array [sample_i]:bool_value -- model trn outputs
          colnames -- [var_i]:str -- name for each of the X inputs
          slicing_x -- array [var_i]:floatval - values for non-sweep vars
          sweep_vars -- list with [sweepvar_i] or [sweepvar_i, sweepvar_j]
            -- If 1 entry, do line plot (1 var), where y-axis is response
            -- If 2 entries, do contour plot (2 vars), where z-axis is response
        """
        # preconditions
        assert X_train.shape[1] == len(colnames) == slicing_x.shape[0], (
            X_train.shape[1],
            len(colnames),
            slicing_x.shape[0],
        )
        assert X_train.shape[0] == ytrue_train.shape[0], (
            X_train.shape[0],
            ytrue_train.shape[0],
        )
        assert sweep_vars is None or len(sweep_vars) in [1, 2]

        # set values
        self.model = model
        self.X_train = X_train
        self.ytrue_train = ytrue_train
        self.colnames = colnames
        self.slicing_x = slicing_x
        self.sweep_vars = sweep_vars

    @property
    @enforce_types
    def n(self) -> int:
        """Number of input dimensions == # columns in X"""
        return self.X_train.shape[1]

    @property
    @enforce_types
    def n_sweep(self) -> int:
        """Number of variables to sweep in the plot"""
        if self.sweep_vars is None:
            return 0

        if self.n == 1:
            return 1

        return len(self.sweep_vars)
