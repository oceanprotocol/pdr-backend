import sys
from typing import Tuple

import numpy as np
import pandas as pd
import polars as pl
from enforce_typing import enforce_types

from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.regressionmodel.regressionmodel_data_factory import (
    RegressionModelDataFactory,
)
from pdr_backend.util.mathutil import fill_nans, has_nan


@enforce_types
class ClassifierModelDataFactory:
    """
    Roles:
    - From mergedohlcv_df, create (X, y, x_df) for model building

    Where
      rawohlcv files -> rawohlcv_dfs -> mergedohlcv_df, via ohlcv_data_factory

      X -- 2d array of [sample_i, var_i] : value -- inputs for model
      y -- 1d array of [sample_i] -- target outputs for model

      x_df -- *pandas* DataFrame with cols like:
        "binanceus:ETH-USDT:open:t-3",
        "binanceus:ETH-USDT:open:t-2",
        "binanceus:ETH-USDT:open:t-1",
        "binanceus:ETH-USDT:high:t-3",
        "binanceus:ETH-USDT:high:t-2",
        "binanceus:ETH-USDT:high:t-1",
        ...
        (no "timestamp" or "datetime" column)
        (and index = 0, 1, .. -- nothing special)

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
    """

    def __init__(self, ss: PredictoorSS):
        self.ss = ss

    def create_xy(
        self,
        mergedohlcv_df: pl.DataFrame,
        testshift: int,
        do_fill_nans: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame, np.ndarray]:
        """
        @arguments
          mergedohlcv_df -- *polars* DataFrame. See class docstring
          testshift -- to simulate across historical test data
          do_fill_nans -- if any values are nan, fill them? (Via interpolation)
            If you turn this off and mergedohlcv_df has nans, then X/y/etc gets nans

        @return --
          X -- 2d array of [sample_i, var_i] : value -- inputs for model
          y -- 1d array of [sample_i] -- target outputs for model where 1 if price went up and 0 otherwise
          x_df -- *pandas* DataFrame. See class docstring.
        """
        factory = RegressionModelDataFactory(self.ss, self.ss.classifiermodel_ss)
        X, y, x_df, xrecent = factory.create_xy(mergedohlcv_df, testshift, do_fill_nans)

        # convert y to 1 if price went up and 0 otherwise compared to y+1
        y = np.array([1 if y[i] < y[i + 1] else 0 for i in range(len(y) - 1)])

        # delete first row of X and x_df
        X = X[1:]
        x_df = x_df.iloc[1:]
        x_df = x_df.reset_index(drop=True)
        xrecent = xrecent[1:]

        return X, y, x_df, xrecent
