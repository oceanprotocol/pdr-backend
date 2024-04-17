import logging
import sys
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import polars as pl

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.util.mathutil import fill_nans, has_nan

logger = logging.getLogger("aimodel_data_factory")


@enforce_types
class AimodelDataFactory:
    """
    Roles:
    - From mergedohlcv_df, create (X, y, x_df, xrecent) for model building

    Where
      rawohlcv files -> rawohlcv_dfs -> mergedohlcv_df, via ohlcv_data_factory

      X -- 2d array of [sample_i, var_i]:value -- inputs for model
      y -- 1d array of [sample_i]:value -- target outputs for model

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

      xrecent -- [var_i]:value -- most recent X value. Bots use to predict

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
    """

    def __init__(self, ss: PredictoorSS):
        self.ss = ss

    @staticmethod
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

    def create_xy(
        self,
        mergedohlcv_df: pl.DataFrame,
        testshift: int,
        predict_feed: ArgFeed,
        train_feeds: Optional[ArgFeeds] = None,
        do_fill_nans: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame, np.ndarray]:
        """
        @description
          Create X, y data for a regression setting
          For y in a classification setting, call ycont_to_ytrue() after.

        @arguments
          mergedohlcv_df -- *polars* DataFrame. See class docstring
          testshift -- to simulate across historical test data
          predict_feed -- feed to predict
          train_feeds -- feeds to use for model inputs. If None use predict feed
          do_fill_nans -- if any values are nan, fill them? (Via interpolation)
            If you turn this off and mergedohlcv_df has nans, then X/y/etc gets nans

        @return
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
          ycont -- 1d array of [sample_i]:cont_value -- regression model outputs
          x_df -- *pandas* DataFrame. See class docstring.
          xrecent -- [var_i]:value -- most recent X value. Bots use to predict
        """
        # preconditions
        assert isinstance(mergedohlcv_df, pl.DataFrame), pl.__class__
        assert "timestamp" in mergedohlcv_df.columns
        assert "datetime" not in mergedohlcv_df.columns

        # condition mergedohlcv_df
        # - every column should be ordered with oldest first, youngest last.
        #  let's verify! The timestamps should be in ascending order
        uts = mergedohlcv_df["timestamp"].to_list()
        assert uts == sorted(uts, reverse=False)
        if do_fill_nans and has_nan(mergedohlcv_df):
            mergedohlcv_df = fill_nans(mergedohlcv_df)

        # condition other inputs
        if not train_feeds:
            train_feeds = [feed]
        ss = self.ss.aimodel_ss
        x_dim_len = len(train_feeds) * ss.autoregressive_n

        # main work
        x_df = pd.DataFrame()  # build this up
        xrecent_df = pd.DataFrame()  # ""

        target_hist_cols = [
            f"{train_feed.exchange}:{train_feed.pair}:{train_feed.signal}"
            for train_feed in train_feeds
        ]
        for hist_col in target_hist_cols:
            assert hist_col in mergedohlcv_df.columns, f"missing data col: {hist_col}"
            z = mergedohlcv_df[hist_col].to_list()  # [..., z(t-2), z(t-1)]
            maxshift = testshift + ss.autoregressive_n
            N_train = min(ss.max_n_train, len(z) - maxshift - 1)
            if N_train <= 0:
                logger.error(
                    "Too little data. len(z)=%d, maxshift=%d "
                    "(= testshift + autoregressive_n = %s + %s)\n"
                    "To fix: broaden time, shrink testshift, "
                    "or shrink autoregressive_n",
                    len(z),
                    maxshift,
                    testshift,
                    ss.autoregressive_n,
                )
                sys.exit(1)
            for delayshift in range(ss.autoregressive_n, 0, -1):  # eg [2, 1, 0]
                shift = testshift + delayshift
                x_col = hist_col + f":t-{delayshift+1}"
                assert (shift + N_train + 1) <= len(z)
                # 1 point for test, the rest for train data
                x_df[x_col] = _slice(z, -shift - N_train - 1, -shift)
                xrecent_df[x_col] = _slice(z, -shift, -shift + 1)

        X = x_df.to_numpy()
        xrecent = xrecent_df.to_numpy()[0, :]

        # y is set from yval_{exch_str, signal_str, pair_str}
        # eg y = [BinEthC_-1, BinEthC_-2, ..., BinEthC_-450, BinEthC_-451]
        hist_col = f"{predict_feed.exchange}:{predict_feed.pair}:{predict_feed.signal}"
        z = mergedohlcv_df[hist_col].to_list()
        y = np.array(_slice(z, -testshift - N_train - 1, -testshift))

        # postconditions
        assert X.shape[0] == y.shape[0]
        assert X.shape[0] <= (ss.max_n_train + 1)
        assert X.shape[1] == x_dim_len
        assert isinstance(x_df, pd.DataFrame)

        assert "timestamp" not in x_df.columns
        assert "datetime" not in x_df.columns

        # return
        ycont = y
        return X, ycont, x_df, xrecent


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
