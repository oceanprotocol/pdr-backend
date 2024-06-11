from typing import Union

from enforce_typing import enforce_types
import numpy as np
from scipy import stats


@enforce_types
def safe_boxcox(y: Union[list, np.ndarray]) -> np.ndarray:
    """
    @description
      Fixes Box-Cox instabilities. Box-Cox can cause problems...
      - it fails outright if min(y) < 0
      - it returns constants if y's are too large, eg around 60e3 (like BTC)

      This method fixes that, by pre-scaling y to N(0,1) plus a positive shift

    @Arguments
      y - [sample_i] : float_value

    @return
      bc_y - [sample_i] : float_transformed_value
    """
    # pre-scale to N(0,1) plus a positive shift
    y = np.array(y)
    mean, std = np.mean(y), np.std(y)
    y = (y - mean) / std
    mn_y = min(y)
    y = y - mn_y + 0.1

    # apply Box-Cox
    y, _ = stats.boxcox(y)

    # un-scale
    y = y + mn_y - 0.1
    y = y * std + mean

    return y  # type: ignore[return-value]
