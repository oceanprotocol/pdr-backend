from enforce_typing import enforce_types
import numpy as np


@enforce_types
def ycont_to_ytrue(ycont: np.ndarray, y_thr: float) -> np.ndarray:
    """
    @description
      Convert regression y (ycont) to classifier y (ybool).

    @arguments
      ycont -- 1d array of [sample_i]:cont_value -- regression model outputs
      y_thr -- classify to True if ycont >= this threshold

    @return
      ybool -- 1d array of [sample_i]:bool_value -- classifier model outputs
    """
    ybool = np.array([ycont_val >= y_thr for ycont_val in ycont])
    return ybool
