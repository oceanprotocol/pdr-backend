from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
import pandas as pd
import polars as pl

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.ppss.aimodel_data_ss import aimodel_data_ss_test_dict
from pdr_backend.ppss.predictoor_ss import (
    PredictoorSS,
    predictoor_ss_test_dict,
)


@enforce_types
def test_create_xy__0__diff012():
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
            max_n_train=4,
            autoregressive_n=3,
            do_diff0=True,
            do_diff1=True,
            do_diff2=True,
        ),
    )
    predictoor_ss = PredictoorSS(d)

    # create df
    timestamps = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    #       t-12 11   10   9    8    7    6    5    4    t-3  t-2
    vals = [8.3, 0.9, 4.2, 2.5, 6.4, 3.6, 8.6, 9.7, 0.5, 0.1, 1.1]
    mergedohlcv_df = pl.DataFrame(
        {
            # every column is ordered from youngest to oldest
            "timestamp": timestamps,  # not used by AimodelDataFactory
            "binanceus:ETH/USDT:close": vals,
        }
    )

    # set target X,y
    target_X = np.array(
        [
            [2.5, 6.4, 3.6, -1.7, 3.9, -2.8, -5.0, 5.6, -6.7],
            [6.4, 3.6, 8.6, 3.9, -2.8, 5.0, 5.6, -6.7, 7.8],
            [3.6, 8.6, 9.7, -2.8, 5.0, 1.1, -6.7, 7.8, -3.9],
            [8.6, 9.7, 0.5, 5.0, 1.1, -9.2, 7.8, -3.9, -10.3],
            [9.7, 0.5, 0.1, 1.1, -9.2, -0.4, -3.9, -10.3, 8.8],
        ]
    )
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:close:z(t-4)": target_X[:, 0],
            "binanceus:ETH/USDT:close:z(t-3)": target_X[:, 1],
            "binanceus:ETH/USDT:close:z(t-2)": target_X[:, 2],
            "binanceus:ETH/USDT:close:z(t-4)-z(t-5)": target_X[:, 3],
            "binanceus:ETH/USDT:close:z(t-3)-z(t-4)": target_X[:, 4],
            "binanceus:ETH/USDT:close:z(t-2)-z(t-3)": target_X[:, 5],
            "binanceus:ETH/USDT:close:(z(t-4)-z(t-5))-(z(t-5)-z(t-6))": target_X[:, 6],
            "binanceus:ETH/USDT:close:(z(t-3)-z(t-4))-(z(t-4)-z(t-5))": target_X[:, 7],
            "binanceus:ETH/USDT:close:(z(t-2)-z(t-3))-(z(t-3)-z(t-4))": target_X[:, 8],
        }
    )

    target_xrecent_d0 = [
        0.5,
        0.1,
        1.1,
    ]
    target_xrecent_d1 = [
        0.5 - 9.7,
        0.1 - 0.5,
        1.1 - 0.1,
    ]
    target_xrecent_d2 = [
        (0.5 - 9.7) - (9.7 - 8.6),
        (0.1 - 0.5) - (0.5 - 9.7),
        (1.1 - 0.1) - (0.1 - 0.5),
    ]
    target_xrecent = np.array(target_xrecent_d0 + target_xrecent_d1 + target_xrecent_d2)

    target_y = np.array([8.6, 9.7, 0.5, 0.1, 1.1])  # oldest to newest

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
    assert X.shape[0] == y.shape[0]
    ss = predictoor_ss.aimodel_data_ss
    assert X.shape[0] == (ss.max_n_train + 1)  # 1 for test, rest for train
    assert len(x_df) == X.shape[0]

    assert_allclose(X, target_X)
    assert_array_equal(y, target_y)
    assert all(x_df.columns == target_x_df.columns)
    assert_allclose(x_df.to_numpy(), target_x_df.to_numpy())
    assert str(x_df) == str(target_x_df)
    assert_allclose(xrecent, target_xrecent)


@enforce_types
def test_create_xy__0__diff1():
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
            max_n_train=4,
            autoregressive_n=3,
            do_diff0=False,
            do_diff1=True,
            do_diff2=False,
        ),
    )
    predictoor_ss = PredictoorSS(d)

    # create df
    timestamps = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    #       t-12 11   10   9    8    7    6    5    4    t-3  t-2
    vals = [8.3, 0.9, 4.2, 2.5, 6.4, 3.6, 8.6, 9.7, 0.5, 0.1, 1.1]
    mergedohlcv_df = pl.DataFrame(
        {
            # every column is ordered from youngest to oldest
            "timestamp": timestamps,  # not used by AimodelDataFactory
            "binanceus:ETH/USDT:close": vals,
        }
    )

    # set target X,y
    target_X = np.array(
        [
            [-1.7, 3.9, -2.8],
            [3.9, -2.8, 5.0],
            [-2.8, 5.0, 1.1],
            [5.0, 1.1, -9.2],
            [1.1, -9.2, -0.4],
        ]
    )
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:close:z(t-4)-z(t-5)": target_X[:, 3],
            "binanceus:ETH/USDT:close:z(t-3)-z(t-4)": target_X[:, 4],
            "binanceus:ETH/USDT:close:z(t-2)-z(t-3)": target_X[:, 5],
        }
    )

    target_xrecent_d1 = [
        0.5 - 9.7,
        0.1 - 0.5,
        1.1 - 0.1,
    ]
    target_xrecent = np.array(target_xrecent_d1)

    target_y = np.array([8.6, 9.7, 0.5, 0.1, 1.1])  # oldest to newest

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
    assert X.shape[0] == y.shape[0]
    ss = predictoor_ss.aimodel_data_ss
    assert X.shape[0] == (ss.max_n_train + 1)  # 1 for test, rest for train
    assert len(x_df) == X.shape[0]

    assert_allclose(X, target_X)
    assert_array_equal(y, target_y)
    assert all(x_df.columns == target_x_df.columns)
    assert_allclose(x_df.to_numpy(), target_x_df.to_numpy())
    assert str(x_df) == str(target_x_df)
    assert_allclose(xrecent, target_xrecent)
