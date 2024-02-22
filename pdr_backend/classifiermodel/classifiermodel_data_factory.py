import sys
from typing import Tuple

import numpy as np
import pandas as pd
import polars as pl
from enforce_typing import enforce_types

from pdr_backend.ppss.predictoor_ss import PredictoorSS
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
    ) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
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
        # preconditions
        assert isinstance(mergedohlcv_df, pl.DataFrame), pl.__class__
        assert "timestamp" in mergedohlcv_df.columns
        assert "datetime" not in mergedohlcv_df.columns

        uts = mergedohlcv_df["timestamp"].to_list()
        assert uts == sorted(uts, reverse=False)

        # condition inputs
        if do_fill_nans and has_nan(mergedohlcv_df):
            mergedohlcv_df = fill_nans(mergedohlcv_df)
        ss = self.ss.classifiermodel_ss

        # main work
        x_df = pd.DataFrame()  # build this up

        target_hist_cols = [
            f"{feed.exchange}:{feed.pair}:{feed.signal}" for feed in ss.feeds
        ]

        for hist_col in target_hist_cols:
            assert hist_col in mergedohlcv_df.columns, f"missing data col: {hist_col}"
            z = mergedohlcv_df[hist_col].to_list()  # [..., z(t-3), z(t-2), z(t-1)]
            maxshift = testshift + ss.autoregressive_n
            N_train = min(ss.max_n_train, len(z) - maxshift - 1)
            if N_train <= 0:
                print(
                    f"Too little data. len(z)={len(z)}, maxshift={maxshift}"
                    " (= testshift + autoregressive_n = "
                    f"{testshift} + {ss.autoregressive_n})\n"
                    "To fix: broaden time, shrink testshift, "
                    "or shrink autoregressive_n"
                )
                sys.exit(1)
            for delayshift in range(ss.autoregressive_n, 0, -1):  # eg [2, 1, 0]
                shift = testshift + delayshift
                x_col = hist_col + f":t-{delayshift+1}"
                assert (shift + N_train + 1) <= len(z)
                # 1 point for test, the rest for train data
                x_df[x_col] = _slice(z, -shift - N_train - 1, -shift)

        X = x_df.to_numpy()

        # calculate y based on price movement: 1 if price increased, 0 otherwise
        ref_ss = self.ss
        hist_col = f"{ref_ss.exchange_str}:{ref_ss.pair_str}:{ref_ss.signal_str}"
        z = mergedohlcv_df[hist_col].to_list()

        start_idx = max(0, len(z) - testshift - N_train - 1)
        end_idx = max(0, len(z) - testshift - 1)
        end_idx = min(end_idx, len(z) - 1)

        y = np.array([1 if z[i + 1] > z[i] else 0 for i in range(start_idx, end_idx)])

        # postconditions
        assert (
            X.shape[0] == y.shape[0]
        ), f"X.shape[0] == y.shape[0] Failed, shapes: {X.shape[0]} != {y.shape[0]}"
        assert X.shape[0] <= (ss.max_n_train + 1)
        assert X.shape[1] == ss.n
        assert isinstance(x_df, pd.DataFrame)
        assert "timestamp" not in x_df.columns
        assert "datetime" not in x_df.columns

        # return
        return X, y, x_df


@enforce_types
def _slice(x: list, st: int, fin: int) -> list:
    """Python list slice returns an empty list on x[st:fin] if st<0 and fin=0
    This overcomes that issue, for cases when st<0"""
    assert st < 0
    assert fin <= 0
    assert st < fin
    if fin == 0:
        return x[st:]
    return x[st:fin]
