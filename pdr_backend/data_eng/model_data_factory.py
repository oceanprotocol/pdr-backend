import sys
from typing import Tuple

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import polars as pl

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.util.mathutil import has_nan, fill_nans


@enforce_types
class ModelDataFactory:
    """
    Roles:
    - From hist_df, create (X, y, x_df) for model building

    Where
      parquet files -> parquet_dfs -> hist_df, via parquet_data_factory

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
        "datetime",
        (and index = 0, 1, .. -- nothing special)

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
       - "datetime" values ares python datetime.datetime, UTC
    """

    def __init__(self, pp: DataPP, ss: DataSS):
        self.pp = pp
        self.ss = ss

    def create_xy(
        self,
        hist_df: pl.DataFrame,
        testshift: int,
        do_fill_nans: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """
        @arguments
          hist_df -- *polars* DataFrame. See class docstring
          testshift -- to simulate across historical test data
          do_fill_nans -- if any values are nan, fill them? (Via interpolation)
            If you turn this off and hist_df has nans, then X/y/etc gets nans

        @return --
          X -- 2d array of [sample_i, var_i] : value -- inputs for model
          y -- 1d array of [sample_i] -- target outputs for model
          x_df -- *pandas* DataFrame. See class docstring.
        """
        # preconditions
        assert isinstance(hist_df, pl.DataFrame), pl.__class__
        assert "timestamp" in hist_df.columns
        assert "datetime" in hist_df.columns

        # every column should be ordered with oldest first, youngest last.
        # let's verify! The timestamps should be in ascending order
        uts = hist_df["timestamp"].to_list()
        assert uts == sorted(uts, reverse=False)

        # condition inputs
        if do_fill_nans and has_nan(hist_df):
            hist_df = fill_nans(hist_df)
        ss = self.ss

        # main work
        x_df = pd.DataFrame()  # build this up

        target_hist_cols = [
            f"{exch_str}:{pair_str}:{signal_str}"
            for exch_str, signal_str, pair_str in ss.input_feed_tups
        ]

        for hist_col in target_hist_cols:
            assert hist_col in hist_df.columns, f"missing data col: {hist_col}"
            z = hist_df[hist_col].to_list()  # [..., z(t-3), z(t-2), z(t-1)]
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

        # y is set from yval_{exch_str, signal_str, pair_str}
        # eg y = [BinEthC_-1, BinEthC_-2, ..., BinEthC_-450, BinEthC_-451]
        pp = self.pp
        hist_col = f"{pp.exchange_str}:{pp.pair_str}:{pp.signal_str}"
        z = hist_df[hist_col].to_list()
        y = np.array(_slice(z, -testshift - N_train - 1, -testshift))

        # postconditions
        assert X.shape[0] == y.shape[0]
        assert X.shape[0] <= (ss.max_n_train + 1)
        assert X.shape[1] == ss.n
        assert isinstance(x_df, pd.DataFrame)

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
