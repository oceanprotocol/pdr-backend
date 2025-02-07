import logging
import sys
from typing import List, Optional, Tuple

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import polars as pl

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.technical_indicators import get_indicator
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

      x_df -- *pandas* DataFrame.
        If transform is "None", cols are like:
          "binanceus:ETH-USDT:open:t-2",
          "binanceus:ETH-USDT:open:t-1",
          "binanceus:ETH-USDT:high:t-2",
          "binanceus:ETH-USDT:high:t-1",

        or, if transform is "RelDiff", cols are like:
          "binanceus:ETH-USDT:open:(z(t-2)-z(t-3))/z(t-3)",
          "binanceus:ETH-USDT:open:(z(t-1)-z(t-2))/z(t-2)",
          "binanceus:ETH-USDT:high:(z(t-2)-z(t-3))/z(t-3)",
          "binanceus:ETH-USDT:high:(z(t-1)-z(t-2))/z(t-2)",

        ...
        (no "timestamp" or "datetime" column)
        (and index = 0, 1, .. -- nothing special)

      xrecent -- [var_i]:value -- most recent X value. Bots use to predict

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
    """

    def __init__(self, ss: PredictoorSS):
        self.ss = ss

    def create_xy(
        self,
        mergedohlcv_df: pl.DataFrame,
        testshift: int,
        predict_feed: ArgFeed,
        train_feeds: Optional[ArgFeeds] = None,
        do_fill_nans: bool = True,
        ta_features: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame, np.ndarray]:
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
            If you turn this off and mergedohlcv_df has nans, it raises error

        @return
          X -- 2d array of [sample_i, var_i]:float -- model inputs
          ytran -- 1d array of [sample_i]:float -- transformed regr outputs. Eg % chg
          yraw -- 1d array of [sample_i]:float. Un-transformed outputs. Eg price
          x_df -- *pandas* DataFrame. See class docstring.
          xrecent -- [var_i]:value -- most recent X value. Bots use to predict
        """
        # pylint: disable=too-many-statements

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
        if has_nan(mergedohlcv_df):
            if not do_fill_nans:
                raise ValueError("We have nans; need to fill them beforehand")
            mergedohlcv_df = fill_nans(mergedohlcv_df)

        # condition other inputs
        train_feeds_list: List[ArgFeed]
        if train_feeds:
            train_feeds_list = train_feeds
        else:
            train_feeds_list = [predict_feed]
        ss = self.ss.aimodel_data_ss
        N_train = ss.max_n_train
        x_dim_len = len(train_feeds_list) * ss.autoregressive_n
        diff = 0 if ss.transform == "None" else 1

        features: List[pd.Series] = []
        if ta_features:
            for feed in train_feeds_list:
                # Generate feed keys
                feed_keys = {
                    key: f"{feed.exchange}:{feed.pair}:{key}"
                    for key in ["close", "open", "high", "low", "volume"]
                }

                for feature in ta_features:
                    ta_class = get_indicator.get_ta_indicator(feature)
                    if ta_class is None:
                        raise ValueError(f"Unknown TA feature: {feature}")

                    ta = ta_class(mergedohlcv_df.to_pandas(), **feed_keys)
                    features.append(ta.calculate())

            # Verify the results
            num_features = len(ta_features) * len(train_feeds_list)
            assert len(features) == num_features
            assert len(features[0]) == len(mergedohlcv_df)
        # main work
        xcol_list = []  # [col_i] : name_str
        x_list = []  # [col_i] : Series. Build this up. Not df here (slow)
        xrecent_list = []  ## ""

        target_hist_cols = [
            hist_col_name(train_feed) for train_feed in train_feeds_list
        ]
        for hist_col in target_hist_cols:
            assert hist_col in mergedohlcv_df.columns, f"missing data col: {hist_col}"
            zraw_series = mergedohlcv_df[hist_col]
            if diff == 0:
                z = zraw_series.to_list()
            else:
                z = zraw_series.pct_change()[1:].to_list()
            maxshift = testshift + ss.autoregressive_n
            if (maxshift + N_train) > len(z):
                s = "Too little data. To fix:"
                s += "broaden time, or shrink testshift, max_diff, or autoregr_n"
                logger.error(s)
                sys.exit(1)

            for delayshift in range(ss.autoregressive_n, 0, -1):  # eg [2, 1, 0]
                shift = testshift + delayshift
                assert (shift + N_train) <= len(z)
                # 1 point for test, the rest for train data
                x_list += [pd.Series(_slice(z, -shift - N_train - 1, -shift))]
                xrecent_list += [pd.Series(_slice(z, -shift, -shift + 1))]

                ds1, ds11 = delayshift + 1, delayshift + 1 + 1
                if diff == 0:
                    x_col = hist_col + f":z(t-{ds1})"
                else:
                    x_col = hist_col + f":(z(t-{ds1})-z(t-{ds11}))/z(t-{ds11})"
                xcol_list += [x_col]

                for i, feature in enumerate(features):
                    assert type(feature) == pd.Series  # type check for mypy
                    feature_np = list(feature.values)
                    features_shifted = pd.Series(
                        _slice(feature_np, -shift - N_train - 1, -shift)
                    )
                    x_list += [features_shifted]
                    xrecent_list += [pd.Series(_slice(feature_np, -shift, -shift + 1))]
                    xcol_list.append(f"{feature.name}_t-{ds1}-{i}")

        # convert x lists to dfs, all at once. Faster than building up df.
        assert len(x_list) == len(xrecent_list) == len(xcol_list)
        x_df = pd.concat(x_list, keys=xcol_list, axis=1)
        xrecent_df = pd.concat(xrecent_list, keys=xcol_list, axis=1)
        assert x_df.shape[0] == N_train + 1  # the +1 is for test

        # convert x dfs to numpy arrays
        X = x_df.to_numpy()
        xrecent = xrecent_df.to_numpy()[0, :]
        assert X.shape[0] == N_train + 1  # the +1 is for test

        # y is set from yval_{exch_str, signal_str, pair_str}
        hist_col = hist_col_name(predict_feed)

        yraw_series = mergedohlcv_df[hist_col]
        yraw_list = yraw_series.to_list()
        yraw = np.array(_slice(yraw_list, -testshift - N_train - 1, -testshift))
        assert X.shape[0] == yraw.shape[0]

        if diff == 0:
            ytran = yraw
        else:
            ytran_list = yraw_series.pct_change()[1:].to_list()
            ytran = np.array(_slice(ytran_list, -testshift - N_train - 1, -testshift))
        assert X.shape[0] == ytran.shape[0]

        # postconditions
        assert X.shape[0] == yraw.shape[0] == ytran.shape[0]
        assert X.shape[0] <= (N_train + 1)
        feature_dims = len(features) * len(train_feeds_list) * ss.autoregressive_n
        assert X.shape[1] == x_dim_len + feature_dims
        assert isinstance(x_df, pd.DataFrame)

        assert "timestamp" not in x_df.columns
        assert "datetime" not in x_df.columns

        # log
        logger.debug("Create model X/y data: done.")

        # return
        return X, ytran, yraw, x_df, xrecent

    def get_highlow(
        self, mergedohlcv_df: pl.DataFrame, feed: ArgFeed, testshift: int
    ) -> tuple:
        shifted_mergedohlcv_df = mergedohlcv_df[-testshift - 2]
        high_col = f"{feed.exchange}:{feed.pair}:high"
        low_col = f"{feed.exchange}:{feed.pair}:low"
        cur_high = shifted_mergedohlcv_df[high_col].to_numpy()[0]
        cur_low = shifted_mergedohlcv_df[low_col].to_numpy()[0]

        return (cur_high, cur_low)


@enforce_types
def hist_col_name(feed: ArgFeed) -> str:
    return f"{feed.exchange}:{feed.pair}:{feed.signal}"


@enforce_types
def _slice(x: list, st: int, fin: int) -> list:
    """Python list slice returns an empty list on x[st:fin] if st<0 and fin=0
    This overcomes that issue, for cases when st<0"""
    assert st < 0
    assert fin <= 0
    assert st < fin
    assert abs(st) <= len(x), f"st is out of bounds. st={st}, len(x)={len(x)}"

    if fin == 0:
        slicex = x[st:]
    else:
        slicex = x[st:fin]

    assert len(slicex) == fin - st, (len(slicex), fin - st, st, fin)
    return slicex
