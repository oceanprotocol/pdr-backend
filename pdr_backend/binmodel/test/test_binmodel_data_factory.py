from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal
import polars as pl

from pdr_backend.binmodel.binmodel_data import BinmodelData
from pdr_backend.binmodel.binmodel_data_factory import BinmodelDataFactory
from pdr_backend.binmodel.constants import UP, DOWN
from pdr_backend.ppss.ppss import mock_ppss, PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS


@enforce_types
def test_binmodel_data_factory__basic():
    # base data
    data_f = _simple_factory()

    # attributes
    assert isinstance(data_f.ppss, PPSS)

    # properties
    assert isinstance(data_f.pdr_ss, PredictoorSS)
    assert isinstance(data_f.class_thr, float)
    assert 0.0 < data_f.class_thr < 1.0


@enforce_types
def test_binmodel_data_factory__testshift():
    # base data
    data_f = _simple_factory()
    test_i = 3

    # do work
    test_n = data_f.ppss.sim_ss.test_n

    # test
    assert data_f.testshift(test_i) == test_n - test_i - 1


@enforce_types
def test_binmodel_data_factory__thr_UP__thr_DOWN():
    # base data
    data_f = _simple_factory()
    cur_close = 8.0
    class_thr: float = data_f.ppss.predictoor_ss.aimodel_data_ss.class_thr

    # do work
    thr_UP = data_f.thr_UP(cur_close)
    thr_DOWN = data_f.thr_DOWN(cur_close)

    # test
    assert class_thr > 0.0
    assert thr_DOWN < cur_close < thr_UP
    assert thr_UP == cur_close * (1 + class_thr)
    assert thr_DOWN == cur_close * (1 - class_thr)


@enforce_types
def _simple_factory() -> BinmodelDataFactory:
    s = "binanceus ETH/USDT c 5m"
    ppss = mock_ppss(feedset_list=[{"predict": s, "train_on": s}])
    return BinmodelDataFactory(ppss)


@enforce_types
def test_binmodel_data_factory__build():
    # =====================
    # raw data

    mergedohlcv_df = pl.DataFrame(
        {
            # every column in df is ordered from youngest to oldest
            #   i.e. [t-1, t-2, t-3, t-4, t-5]
            "timestamp": [1, 2, 3, 4, 5],
            "binanceus:ETH/USDT:high": [70.0, 69.0, 67.0, 68.0, 48.0],
            "binanceus:ETH/USDT:low": [65.0, 61.0, 59.0, 62.0, 42.0],
            "binanceus:ETH/USDT:close": [60.0, 66.0, 167.0, 64.0, 44.0],
        }
    )

    # =====================
    # configure the problem
    feed_s = "binanceus ETH/USDT c 5m"
    ppss = mock_ppss(feedset_list=[{"predict": feed_s, "train_on": feed_s}])
    ppss.predictoor_ss.aimodel_data_ss.set_max_n_train(2)
    ppss.predictoor_ss.aimodel_data_ss.set_autoregressive_n(1)
    ppss.sim_ss.set_test_n(1)
    test_i = 0

    # =====================
    # set targets
    # no. rows of X = len(y) = max_n_train + max_n_test(=1) = 2 + 1 = 3
    # no. cols of X = autoregressive_n * num_signals = 1 * 3  = 3
    target_X_UP = np.array(
        [  # h, l, c
            [69.0, 61.0, 66.0],  # oldest
            [67.0, 59.0, 167.0],
            [68.0, 62.0, 64.0],  # newest
        ]
    )

    # calculated from cur_close = [167, 64, 44],
    # next_low = [61, 59, 62], and next_high = [67, 68, 48]
    target_ytrue_UP = np.array([False, True, True])

    # =====================
    # main work
    binmodel_data_factory = BinmodelDataFactory(ppss)
    binmodel_data = binmodel_data_factory.build(test_i, mergedohlcv_df)

    # =====================
    # check results
    X_UP = binmodel_data[UP].X
    ytrue_UP = binmodel_data[UP].ytrue

    assert_array_equal(X_UP, target_X_UP)
    assert_array_equal(ytrue_UP, target_ytrue_UP)
