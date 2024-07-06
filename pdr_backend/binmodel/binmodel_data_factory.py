from typing import List, Tuple

from enforce_typing import enforce_types
import numpy as np
import polars as pl

from pdr_backend.binmodel.binmodel_data import BinmodelData, BinmodelData1Dir
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS


class BinmodelDataFactory:
    @enforce_types
    def __init__(self, ppss: PPSS):
        self.ppss = ppss

    @property
    def pdr_ss(self) -> PredictoorSS:
        return self.ppss.predictoor_ss

    @property
    def class_thr(self) -> float:
        return self.pdr_ss.aimodel_data_ss.class_thr

    @property
    def predict_feed(self) -> ArgFeed:
        return self.pdr_ss.predict_train_feedsets[0].predict

    @enforce_types
    def feed_variant(self, signal_str: str) -> ArgFeed:
        assert signal_str in ["close", "high", "low"]
        return self.predict_feed.variant_signal(signal_str)

    @property
    def max_n_train(self) -> float:
        return self.pdr_ss.aimodel_data_ss.max_n_train

    def set_max_n_train(self, n: int) -> float:
        return self.pdr_ss.aimodel_data_ss.set_max_n_train(n)

    def testshift(self, test_i: int) -> int:
        test_n = self.ppss.sim_ss.test_n
        return AimodelDataFactory.testshift(test_n, test_i)

    @enforce_types
    def build(self, test_i: int, mergedohlcv_df: pl.DataFrame) -> BinmodelData:
        """Construct sim model data"""
        # main work
        X, colnames = self._build_X(test_i, mergedohlcv_df)
        ytrue_UP, ytrue_DOWN = self._build_ytrue(test_i, mergedohlcv_df)

        # key check
        assert (
            X.shape[0] == ytrue_UP.shape[0] == ytrue_DOWN.shape[0]
        ), "X and y must have same # samples"

        # build final object, return
        d_UP = BinmodelData1Dir(X, ytrue_UP, colnames)
        d_DOWN = BinmodelData1Dir(X, ytrue_DOWN, colnames)
        d = BinmodelData(d_UP, d_DOWN)
        return d

    @enforce_types
    def _build_X(self, test_i: int, df) -> Tuple[np.ndarray, List[str]]:
        """
        @description
          Build X for training/testing both UP and DOWN models.
          (It could be same or different for both. Here, it's the same.)

        @return
          X -- 2d array [sample_i][var_i]
          colnames -- list [var_i] of str
        """
        # base data
        data_f = AimodelDataFactory(self.pdr_ss)
        testshift = self.testshift(test_i)  # eg [99, 98, .., 2, 1, 0]

        # main work
        X, _, _, x_df, _ = data_f.create_xy(
            df,
            testshift,
            self.feed_variant("low"),  # arbitrary
            ArgFeeds(
                [
                    self.feed_variant("high"),
                    self.feed_variant("low"),
                    self.feed_variant("close"),
                ]
            ),
        )
        colnames = list(x_df.columns)

        # We don't need to split X/y into train & test here.
        #   Rather, it happens inside BinmodelFactory.build()
        #   which calls BinmodelData1Dir.X_train(), ytrue_train(), and X_test()

        # done
        return (X, colnames)

    @enforce_types
    def _build_ytrue(self, test_i: int, df) -> Tuple[np.ndarray, np.ndarray]:
        """
        @description
          Build y for training/testing both UP and DOWN models.
          (It's usually different for UP vs down; and that's the case here.)
        @return
          ytrue_UP -- [sample_i] : bool -- outputs for training UP model
          ytrue_DOWN -- [sample_i] : bool -- outputs for training DOWN model
        """
        # grab y_close/high/low from df
        # y_close, etc are in order from youngest to oldest, ie t-1, t-2, ..
        y_close = self._y_incl_extra_sample(test_i, df, "close")
        y_high = self._y_incl_extra_sample(test_i, df, "high")
        y_low = self._y_incl_extra_sample(test_i, df, "low")

        # for 'next', truncate oldest entry (at end)
        y_next_high, y_next_low = y_high[:-1], y_low[:-1]

        # for 'cur' (prev), truncate newest entry (at front)
        y_cur_close = y_close[1:]

        # construct ytrue_UP/DOWN lists from comparing high/low to close+/-%
        ytrue_UP_list, ytrue_DOWN_list = [], []
        for cur_close, next_high, next_low in zip(y_cur_close, y_next_high, y_next_low):

            # did the next high value go above the current close+% value?
            thr_UP = self.thr_UP(cur_close)
            ytrue_UP_list.append(next_high > thr_UP)

            # did the next low value go below the current close-% value?
            thr_DOWN = self.thr_DOWN(cur_close)
            ytrue_DOWN_list.append(next_low < thr_DOWN)

        # final conditioning, return
        ytrue_UP = np.array(ytrue_UP_list)
        ytrue_DOWN = np.array(ytrue_DOWN_list)
        return (ytrue_UP, ytrue_DOWN)

    @enforce_types
    def _y_incl_extra_sample(self, test_i: int, df, signal_str: str) -> np.ndarray:
        """
        @description

         We need an extra sample because
         - each value of ytrue is from computed from two different candles
           (next_*, cur_*), which would naturally reduce total # samples by 1
         - yet we still want the resulting ytrue to have same # samples as X
         To get that extra sample, we temporarily set max_n_train += 1
        """
        assert signal_str in ["close", "high", "low"]

        self.set_max_n_train(self.max_n_train + 1)
        testshift = self.testshift(test_i)  # eg [99, 98, .., 2, 1, 0]

        data_f = AimodelDataFactory(self.pdr_ss)
        _, _, y, _, _ = data_f.create_xy(
            df,
            testshift,
            self.feed_variant(signal_str),
            ArgFeeds([self.feed_variant(signal_str)]),
        )
        assert len(y) == self.max_n_train + 1  # num_train + num_test(=1)
        self.set_max_n_train(self.max_n_train - 1)
        return y

    @enforce_types
    def thr_UP(self, cur_close: float) -> float:
        return cur_close * (1 + self.class_thr)

    @enforce_types
    def thr_DOWN(self, cur_close: float) -> float:
        return cur_close * (1 - self.class_thr)
