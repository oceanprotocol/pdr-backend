import logging
import os
from typing import Tuple

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.util.strutil import pad_with_zeroes

log = logging.getLogger("xycsv")


class XycsvMgr:
    """Save X,y to disk and load again"""

    def __init__(self, xy_dir: str, runid: int):
        self.xy_dir = xy_dir
        self.runid = runid
        self.saved_iters = []

    @enforce_types
    def save_xy(self, X: np.ndarray, y: np.ndarray, iter_number: int) \
            -> Tuple[str,str]:
        if self.xy_dir == "None":
            return ("", "")
        assert X.shape[0] == y.shape[0]

        xy_dir = self.abs_xy_dir
        if not os.path.exists(xy_dir):
            log.info("xy_dir doesn't exist; creating it: %s", xy_dir)
            os.mkdir(xy_dir)

        run_dir = self.abs_run_dir
        if not os.path.exists(run_dir):
            log.info("in xy_dir, run_dir doesn't exist; creating it: %s ", run_dir)
            os.mkdir(run_dir)

        x_filename, y_filename = self.abs_xy_filenames(iter_number)

        np.savetxt(x_filename, X, fmt="%.6f")
        np.savetxt(y_filename, y, fmt="%.6f")

        self.saved_iters.append(iter_number)

        return (x_filename, y_filename)

    @enforce_types
    def load_xy(self, iter_number: int):
        x_filename, y_filename = self.abs_xy_filenames(iter_number)
        X = np.loadtxt(x_filename)
        y = np.loadtxt(y_filename)

        # corner case: 1 input dimension
        if len(X.shape) == 1:
            X = X.reshape(X.shape[0], 1)
        return (X, y)

    @property
    def abs_xy_dir(self) -> str:
        return os.path.abspath(self.xy_dir)

    @property
    def abs_run_dir(self) -> str:
        return os.path.join(self.abs_xy_dir, f"run_{self.runid}")

    @enforce_types
    def abs_xy_filenames(self, iter_number: int) -> Tuple[str, str]:
        s_iter = pad_with_zeroes(iter_number, 6)
        x_filename = os.path.join(self.abs_run_dir, f"{s_iter}_X.csv")
        y_filename = os.path.join(self.abs_run_dir, f"{s_iter}_y.csv")
        return (x_filename, y_filename)
