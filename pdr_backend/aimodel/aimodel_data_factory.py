import logging
import sys
from typing import List, Optional, Tuple

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

        # log
        logger.debug("Create model X/y data: begin.")

        # condition mergedohlcv_df
        # - every column should be ordered with oldest first, youngest last.
        #  let's verify! The timestamps should be in ascending order
        uts = mergedohlcv_df["timestamp"].to_list()
        assert uts == sorted(uts, reverse=False)
        if do_fill_nans and has_nan(mergedohlcv_df):
            mergedohlcv_df = fill_nans(mergedohlcv_df)

        # condition other inputs
        train_feeds_list: List[ArgFeed]
        if train_feeds:
            train_feeds_list = train_feeds
        else:
            train_feeds_list = [predict_feed]
        ss = self.ss.aimodel_data_ss
        x_dim_len = len(train_feeds_list) * ss.autoregressive_n * (1 + ss.max_diff)

        # main work
        xcol_list = []  # [col_i] : name_str
        x_list = []  # [col_i] : Series. Build this up. Not df here (slow)
        xrecent_list = []  ## ""

        target_hist_cols = [
            f"{train_feed.exchange}:{train_feed.pair}:{train_feed.signal}"
            for train_feed in train_feeds_list
        ]
        for hist_col in target_hist_cols:
            assert hist_col in mergedohlcv_df.columns, f"missing data col: {hist_col}"
            z_d0 = mergedohlcv_df[hist_col].to_numpy()  # [..., z(t-2), z(t-1)]
            z_d1 = z_d0[1:] - z_d0[:-1]  # [..., z(t-2) - z(t-3),    z(t-1) - z(t-2)]
            z_d2 = z_d1[1:] - z_d1[:-1]  # [...,     (z(t-1)-z(t-2)) - z(t-2)-z(t-3)]
            z_d0, z_d1, z_d2 = list(z_d0), list(z_d1), list(z_d2)
            maxshift = testshift + ss.autoregressive_n
            N_train = min(ss.max_n_train, len(z_d0) - maxshift - 1 - ss.max_diff)
            s = "\n"
            s += f"  ss.autoregressive_n={ss.autoregressive_n}\n"
            s += f"  ss.max_n_train={ss.max_n_train}; ss.max_diff={ss.max_diff}\n"
            s += f"  testshift={testshift}\n"
            s += f"  maxshift=autoregressive_n+testshift={maxshift}\n"
            s += f"  len(z_d0)={len(z_d0)}, len(z_d1)={len(z_d1)}, len(z_d2)={len(z_d2)}\n"
            s += f"  N_train={N_train}\n"
            logger.debug("\n" + s)
            if N_train <= 0:
                s = "Too little data."
                s += (
                    "To fix: broaden time, or shrink testshift, max_diff, or autoregr_n"
                )
                logger.error(s)
                sys.exit(1)

            for diff in range(ss.max_diff + 1):
                logger.info("diff=%s" % diff)
                for delayshift in range(
                    ss.autoregressive_n, 0, -1
                ):  # eg [4, 3, 2, 1, 0]
                    shift = testshift + delayshift
                    # 1 point for test, the rest for train data. For each of diff=0, 1, 2
                    if diff == 0:
                        assert (shift + N_train + 1) <= len(z_d0)
                        x_col_d0 = hist_col + f":z(t-{delayshift+1})"
                        xcol_list += [x_col_d0]
                        x_list += [
                            pd.Series(_slice(z_d0, -shift - N_train - 1, -shift))
                        ]
                        xrecent_list += [pd.Series(_slice(z_d0, -shift, -shift + 1))]

                    if diff == 1:
                        assert (shift + N_train + 1) <= len(z_d1)
                        x_col_d1 = (
                            hist_col + f":z(t-{delayshift+1})-z(t-{delayshift+1+1})"
                        )
                        xcol_list += [x_col_d1]
                        x_list += [
                            pd.Series(_slice(z_d1, -shift - N_train - 1, -shift))
                        ]
                        xrecent_list += [pd.Series(_slice(z_d1, -shift, -shift + 1))]

                    if diff == 2:
                        assert (shift + N_train + 1) <= len(z_d2)
                        x_col_d2 = (
                            hist_col + f":(z(t-{delayshift+1})-z(t-{delayshift+1+1}))-"
                            f"(z(t-{delayshift+1+1})-z(t-{delayshift+1+1+1}))"
                        )
                        xcol_list += [x_col_d2]
                        x_list += [
                            pd.Series(_slice(z_d2, -shift - N_train - 1, -shift))
                        ]
                        xrecent_list += [pd.Series(_slice(z_d2, -shift, -shift + 1))]

        # convert x lists to dfs, all at once. Faster than building up df.
        assert len(x_list) == len(xrecent_list) == len(xcol_list)
        x_df = pd.concat(x_list, keys=xcol_list, axis=1)
        xrecent_df = pd.concat(xrecent_list, keys=xcol_list, axis=1)

        # convert x dfs to numpy arrays
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

        # log
        logger.debug("Create model X/y data: done.")

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
