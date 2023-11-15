from math import log10, floor
import random
import re
from typing import Union

from enforce_typing import enforce_types
import numpy as np
import pandas as pd

from pdr_backend.util.strutil import StrMixin


@enforce_types
def isNumber(x) -> bool:
    return isinstance(x, (int, float))


@enforce_types
def intInStr(s: str) -> int:
    int_s = re.sub("[^0-9]", "", s)
    return int(int_s)


@enforce_types
class Range(StrMixin):
    def __init__(self, min_: float, max_: Union[float, None] = None):
        assert (max_ is None) or (max_ >= min_)
        self.min_: float = min_
        self.max_: Union[float, None] = max_

    def drawRandomPoint(self) -> float:
        if self.max_ is None:
            return self.min_
        return randunif(self.min_, self.max_)


@enforce_types
def randunif(mn: float, mx: float) -> float:
    """Return a uniformly-distributed random number in range [mn, mx]"""
    assert mx >= mn
    if mn == mx:
        return mn
    return mn + random.random() * (mx - mn)


@enforce_types
def round_sig(x: Union[int, float], sig: int) -> Union[int, float]:
    """Return a number with the specified # significant bits"""
    return round(x, sig - int(floor(log10(abs(x)))) - 1)


@enforce_types
def has_nan(x: Union[np.ndarray, pd.DataFrame, pd.Series]) -> bool:
    """Returns True if any entry in x has a nan"""
    if type(x) == np.ndarray:
        return np.isnan(np.min(x))
    if type(x) in [pd.DataFrame, pd.Series]:
        return x.isnull().values.any()  # type: ignore[union-attr]
    raise ValueError(f"Can't handle type {type(x)}")


@enforce_types
def fill_nans(df: pd.DataFrame) -> pd.DataFrame:
    """Interpolate the nans using Linear method.
    It ignores the index and treat the values as equally spaced.

    Ref: https://www.geeksforgeeks.org/working-with-missing-data-in-pandas/
    """
    df = df.interpolate(method="linear", limit_direction="forward")
    df = df.interpolate(method="linear", limit_direction="backward")  # row 0
    return df


@enforce_types
def nmse(yhat, y, ymin=None, ymax=None) -> float:
    """
    @description
        Calculates the normalized mean-squared error.
    @arguments
        yhat -- 1d array or list of floats -- estimated values of y
        y -- 1d array or list of floats -- true values
        ymin, ymax -- float, float -- roughly the min and max; they
          do not have to be the perfect values of min and max, because
          they're just here to scale the output into a roughly [0,1] range
    @return
        nmse -- float -- normalized mean-squared error
    """
    assert len(y) == len(yhat)
    y, yhat = np.asarray(y), np.asarray(yhat)

    # base case: no entries
    if len(yhat) == 0:
        return 0.0

    # condition ymin, ymax
    if ymin is None and ymax is None:
        ymin, ymax = min(y), max(y)
    assert ymin is not None
    assert ymax is not None

    # base case: both yhat and y are constant, and same values
    if (ymax == ymin) and (max(yhat) == min(yhat) == max(y) == min(y)):
        return 0.0

    # yrange
    yrange = ymax - ymin

    # First, scale true values and predicted values such that:
    # - true values are in range [0.0, 1.0]
    # - predicted values follow the same scaling factors
    y01 = (y - ymin) / yrange
    yhat01 = (yhat - ymin) / yrange

    mse_xy = np.sum(np.square(y01 - yhat01))
    mse_x = np.sum(np.square(y01))
    nmse_result = mse_xy / mse_x

    return nmse_result
