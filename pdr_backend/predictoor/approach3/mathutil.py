import math

import numpy as np
from enforce_typing import enforce_types


@enforce_types
def nmse(yhat, y, min_y=None, max_y=None):  # from nmse library
    """
    @description
        Calculates the normalized mean-squared error.
    @arguments
        yhat -- 1d array or list of floats -- estimated values of y
        y -- 1d array or list of floats -- true values
        min_y, max_y -- float, float -- roughly the min and max; they
          do not have to be the perfect values of min and max, because
          they're just here to scale the output into a roughly [0,1] range
    @return
        nmse -- float -- normalized mean-squared error
    """
    # base case: no entries
    if len(yhat) == 0:
        return 0.0

    # base case: both yhat and y are constant, and same values
    if (max_y == min_y) and (max(yhat) == min(yhat) == max(y) == min(y)):
        return 0.0

    # condition min_y, max_y
    if min_y is None and max_y is None:
        min_y, max_y = min(y), max(y)
    assert min_y is not None
    assert max_y is not None

    # main case
    assert max_y > min_y, "max_y=%g was not > min_y=%g" % (max_y, min_y)
    yhat_a, y_a = np.asarray(yhat), np.asarray(y)
    y_range = float(max_y - min_y)

    result = math.sqrt(np.mean(((yhat_a - y_a) / y_range) ** 2))
    if np.isnan(result):
        # TODO: leftover from tlmplay. Adjust?
        return INF
    return result
