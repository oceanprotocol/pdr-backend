from enforce_typing import enforce_types
import numpy as np
import polars as pl

from pdr_backend.binmodel.binmodel_data import BinmodelData
from pdr_backend.binmodel.binmodel_data_factory import BinmodelDataFactory
from pdr_backend.binmodel.constants import UP, DOWN
from pdr_backend.ppss.ppss import mock_ppss, PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS


@enforce_types
def test_binmodel_data_factory__basic():
    # base data
    data_f = _factory()

    # attributes
    assert isinstance(data_f.ppss, PPSS)

    # properties
    assert isinstance(data_f.pdr_ss, PredictoorSS)
    assert isinstance(data_f.class_thr, float)
    assert 0.0 < data_f.class_thr < 1.0


@enforce_types
def test_binmodel_data_factory__testshift():
    # base data
    data_f = _factory()
    test_i = 3

    # do work
    test_n = data_f.ppss.sim_ss.test_n

    # test
    assert data_f.testshift(test_i) == test_n - test_i - 1


@enforce_types
def test_binmodel_data_factory__thr_UP__thr_DOWN():
    # base data
    data_f = _factory()
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
def test_binmodel_data_factory__build():
    # base data
    mergedohlcv_df = _merged_ohlcv_df()
    data_f = _factory()
    test_i = 0

    # do work
    data = data_f.build(test_i, mergedohlcv_df)

    # test
    # - keep this light for now. Maybe expand when things stabilize
    assert isinstance(data, BinmodelData)
    assert 9.0 < np.min(data[UP].X) < np.max(data[UP].X) < 9.99  # all 'high'
    assert 0.0 < np.min(data[DOWN].X) < np.max(data[DOWN].X) < 0.99  # all 'low'


@enforce_types
def _factory() -> BinmodelDataFactory:
    s = "binanceus ETH/USDT c 5m"
    feedset_list = [{"predict": s, "train_on": s}]
    ppss = mock_ppss(feedset_list)

    # change settings so that the factory can work with a small # datapoints
    ppss.predictoor_ss.aimodel_data_ss.set_max_n_train(4)
    ppss.predictoor_ss.aimodel_data_ss.set_autoregressive_n(1)
    ppss.sim_ss.set_test_n(2)

    data_f = BinmodelDataFactory(ppss)
    return data_f


@enforce_types
def _merged_ohlcv_df() -> pl.DataFrame:
    d = {
        # - every column in df is ordered from youngest to oldest
        # - high values are 9.x, 9.y, ..; low are 0.x, 0.y, ..; close is b/w
        "timestamp": [1, 2, 3, 4, 5, 6, 7],
        "binanceus:ETH/USDT:high": [9.1, 9.6, 9.8, 9.4, 9.2, 9.5, 9.7],
        "binanceus:ETH/USDT:low": [0.1, 0.6, 0.8, 0.4, 0.2, 0.5, 0.7],
        "binanceus:ETH/USDT:close": [2.1, 3.6, 4.6, 5.6, 6.2, 7.5, 8.7],
    }
    return pl.DataFrame(d)
