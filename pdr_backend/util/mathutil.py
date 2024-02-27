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
def classif_acc(ytrue_hat, ytrue) -> float:
    ytrue_hat, ytrue = np.array(ytrue_hat), np.array(ytrue)
    n_correct = sum(ytrue_hat == ytrue)
    acc = n_correct / len(ytrue)
    return acc


@enforce_types
def string_to_bytes32(data) -> bytes:
    if len(data) > 32:
        myBytes32 = data[:32]
    else:
        myBytes32 = data.ljust(32, "0")
    return bytes(myBytes32, "utf-8")
