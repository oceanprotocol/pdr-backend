from math import floor, log10
from typing import Union

import numpy as np
import pandas as pd
import polars as pl
from enforce_typing import enforce_types


@enforce_types
def round_sig(x: Union[int, float], sig: int) -> Union[int, float]:
    """Return a number with the specified # significant bits"""
    return round(x, sig - int(floor(log10(abs(x)))) - 1)


@enforce_types
def all_nan(
    x: Union[np.ndarray, pd.DataFrame, pd.Series, pl.DataFrame, pl.Series]
) -> bool:
    """Returns True if all entries in x have a nan _or_ a None"""
    if isinstance(x, np.ndarray):
        x = np.array(x, dtype=float)
        return np.isnan(x).all()

    if isinstance(x, pd.Series):
        x = x.fillna(value=np.nan, inplace=False)
        return x.isnull().all()

    if isinstance(x, pd.DataFrame):
        x = x.fillna(value=np.nan)
        return x.isnull().all().all()

    # pl.Series or pl.DataFrame
    return all_nan(x.to_numpy())  # type: ignore[union-attr]


@enforce_types
def has_nan(
    x: Union[np.ndarray, pd.DataFrame, pd.Series, pl.DataFrame, pl.Series]
) -> bool:
    """Returns True if any entry in x has a nan _or_ a None"""
    if isinstance(x, np.ndarray):
        has_None = (x == None).any()  # pylint: disable=singleton-comparison
        return has_None or np.isnan(np.min(x))

    if isinstance(x, pl.Series):
        has_None = x.has_validity()
        return has_None or sum(x.is_nan()) > 0  # type: ignore[union-attr]

    if isinstance(x, pl.DataFrame):
        has_None = any(col.has_validity() for col in x)
        return has_None or sum(sum(x).is_nan()) > 0  # type: ignore[union-attr]

    # pd.Series or pd.DataFrame
    return x.isnull().values.any()  # type: ignore[union-attr]


@enforce_types
def fill_nans(
    df: Union[pd.DataFrame, pl.DataFrame]
) -> Union[pd.DataFrame, pl.DataFrame]:
    """Interpolate the nans using Linear method available in pandas.
    It ignores the index and treat the values as equally spaced.

    Ref: https://www.geeksforgeeks.org/working-with-missing-data-in-pandas/
    """
    interpolate_df = pd.DataFrame()
    output_type = type(df)

    # polars support
    if output_type == pl.DataFrame:
        interpolate_df = df.to_pandas()
    else:
        interpolate_df = df

    # interpolate is a pandas-only feature
    interpolate_df = interpolate_df.interpolate(
        method="linear", limit_direction="forward"
    )
    interpolate_df = interpolate_df.interpolate(
        method="linear", limit_direction="backward"
    )  # row 0

    # return polars if input was polars
    if type(output_type) == pl.DataFrame:
        interpolate_df = pl.from_pandas(interpolate_df)

    return interpolate_df


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


@enforce_types
def from_wei(amt_wei: int) -> Union[int, float]:
    return float(amt_wei / 1e18)


@enforce_types
def to_wei(amt_eth: Union[int, float]) -> int:
    return int(amt_eth * 1e18)


@enforce_types
def str_with_wei(amt_wei: int) -> str:
    return f"{from_wei(amt_wei)} ({amt_wei} wei)"


@enforce_types
def string_to_bytes32(data) -> bytes:
    if len(data) > 32:
        myBytes32 = data[:32]
    else:
        myBytes32 = data.ljust(32, "0")
    return bytes(myBytes32, "utf-8")
