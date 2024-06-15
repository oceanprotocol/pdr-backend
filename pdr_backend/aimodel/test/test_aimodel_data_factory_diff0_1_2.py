from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd
import polars as pl
import pytest

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.lake.merge_df import merge_rawohlcv_dfs
from pdr_backend.lake.test.resources import (
    BINANCE_BTC_DATA,
    BINANCE_ETH_DATA,
    ETHUSDT_RAWOHLCV_DFS,
    KRAKEN_BTC_DATA,
    KRAKEN_ETH_DATA,
    _df_from_raw_data,
    _mergedohlcv_df_ETHUSDT,
)
from pdr_backend.ppss.aimodel_data_ss import (
    AimodelDataSS,
    aimodel_data_ss_test_dict,
)
from pdr_backend.ppss.predictoor_ss import (
    PredictoorSS,
    predictoor_ss_test_dict,
)
from pdr_backend.util.mathutil import fill_nans, has_nan


@enforce_types
def test_create_xy__0__diff_0_1_2():
    # create predictoor_ss
    feedset_list = [
        {
            "predict": "binanceus ETH/USDT c 5m",
            "train_on": "binanceus ETH/USDT c 5m",
        }
    ]
    d = predictoor_ss_test_dict(
        feedset_list=feedset_list,
        aimodel_data_ss_dict=aimodel_data_ss_test_dict(
            max_n_train=6,
            autoregressive_n=3,
            max_diff=0, # FIXME to 2 # main setting: 2 not 0
        ),
    )
    
    predictoor_ss = PredictoorSS(d)

    # create df
    mergedohlcv_df = pl.DataFrame(
        {
            # every column is ordered from youngest to oldest
            "timestamp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],  # not used by AimodelDataFactory
            "binanceus:ETH/USDT:close":
            [0.3, 0.9, 4.2, 2.5, 6.4, 3.6, 8.6, 9.7, 0.5, 0.1, 1.1],
        }
    )

    # set target X,y
    target_X = np.array(
        [
            [0.9, 4.2, 2.5],  # oldest
            [4.2, 2.5, 6.4],
            [2.5, 6.4, 3.6],
            [6.4, 3.6, 8.6],
            [3.6, 8.6, 9.7],  
            [8.6, 9.7, 0.5],
            [9.7, 0.5, 0.1],  # newest
        ]
    )
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:close:z(t-4)": [0.9, 4.2, 2.5, 6.4, 3.6, 8.6, 9.7],
            "binanceus:ETH/USDT:close:z(t-3)": [4.2, 2.5, 6.4, 3.6, 8.6, 9.7, 0.5],
            "binanceus:ETH/USDT:close:z(t-2)": [2.5, 6.4, 3.6, 8.6, 9.7, 0.5, 0.1],
            #"binanceus:ETH/USDT:close:z(t-4)-z(t-3)": 
            #"binanceus:ETH/USDT:close:z(t-3)-z(t-2)": 
        }
    )
    target_xrecent = np.array([0.5, 0.1, 1.1])

    target_y = np.array([6.4, 3.6, 8.6, 9.7, 0.5, 0.1, 1.1])  # oldest to newest

    # do work
    testshift = 0
    factory = AimodelDataFactory(predictoor_ss)
    predict_feed = predictoor_ss.predict_train_feedsets[0].predict
    train_feeds = predictoor_ss.predict_train_feedsets[0].train_on
    X, y, x_df, xrecent = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    # test result
    _assert_pd_df_shape(predictoor_ss.aimodel_data_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)
    assert_array_equal(xrecent, target_xrecent)


    
# ====================================================================
# utilities


@enforce_types
def _assert_pd_df_shape(
    ss: AimodelDataSS, X: np.ndarray, y: np.ndarray, x_df: pd.DataFrame
):
    assert X.shape[0] == y.shape[0]
    assert X.shape[0] == (ss.max_n_train + 1)  # 1 for test, rest for train

    assert len(x_df) == X.shape[0]
