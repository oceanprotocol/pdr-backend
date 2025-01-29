import os
import time
from typing import Tuple

from enforce_typing import enforce_types
import numpy as np


@enforce_types
def save_xy(X: np.ndarray, y: np.ndarray, filepath: str) -> Tuple[str, str]:
    """
    @description
      Save X, y data to csv

    @arguments
      X -- 2d array of [sample_i, var_i]:float -- model inputs
      y -- 1d array of [sample_i]:float -- model outputs. Eg price
      filepath -- path for the filename

    @return
      X_filename -- for X data, a filepath + auto_generated_filename
      y_filename -- for y data, ""
    """
    assert X.shape[0] == y.shape[0]

    # set names
    s = str(time.time()).replace(".", "")
    X_filename = os.path.join(filepath, f"X_{s}.csv")
    y_filename = os.path.join(filepath, f"y_{s}.csv")

    # write files
    np.savetxt(X_filename, X, fmt="%.6f")
    np.savetxt(y_filename, y, fmt="%.6f")

    return (X_filename, y_filename)


@enforce_types
def load_xy(X_filename: str, y_filename: str) -> Tuple[np.ndarray, np.ndarray]:
    X = np.loadtxt(X_filename)
    y = np.loadtxt(y_filename)
    return (X, y)
