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
def test_create_xy_notransform_main():
    # create predictoor_ss
    feedset_list = [
        {
            "predict": "binanceus ETH/USDT c 5m",
            "train_on": "binanceus ETH/USDT oc 5m",
        }
    ]
    d = predictoor_ss_test_dict(
        feedset_list=feedset_list,
        aimodel_data_ss_dict=aimodel_data_ss_test_dict(
            max_n_train=4, autoregressive_n=2
        ),
    )

    predictoor_ss = PredictoorSS(d)

    # create df
    mergedohlcv_df = pl.DataFrame(
        {
            # every column is ordered from youngest to oldest
            "timestamp": [1, 2, 3, 4, 5, 6, 7, 8],  # not used by AimodelDataFactory
            # The underlying AR process is: close[t] = close[t-1] + open[t-1]
            "binanceus:ETH/USDT:open": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            "binanceus:ETH/USDT:close": [2.0, 3.1, 4.2, 5.3, 6.4, 7.5, 8.6, 9.7],
        }
    )

    # set target X,y
    target_X = np.array(
        [
            [0.1, 0.1, 3.1, 4.2],  # oldest
            [0.1, 0.1, 4.2, 5.3],
            [0.1, 0.1, 5.3, 6.4],
            [0.1, 0.1, 6.4, 7.5],
            [0.1, 0.1, 7.5, 8.6],  # newest
        ]
    )
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:open:z(t-3)": [0.1, 0.1, 0.1, 0.1, 0.1],
            "binanceus:ETH/USDT:open:z(t-2)": [0.1, 0.1, 0.1, 0.1, 0.1],
            "binanceus:ETH/USDT:close:z(t-3)": [3.1, 4.2, 5.3, 6.4, 7.5],
            "binanceus:ETH/USDT:close:z(t-2)": [4.2, 5.3, 6.4, 7.5, 8.6],
        }
    )
    target_xrecent = np.array([0.1, 0.1, 8.6, 9.7])

    target_y = np.array([5.3, 6.4, 7.5, 8.6, 9.7])  # oldest to newest

    # do work
    testshift = 0
    factory = AimodelDataFactory(predictoor_ss)
    predict_feed = predictoor_ss.predict_train_feedsets[0].predict
    train_feeds = predictoor_ss.predict_train_feedsets[0].train_on
    X, y, _, x_df, xrecent = factory.create_xy(
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


@enforce_types
def test_create_xy_notransform__1exchange_1coin_1signal():
    feedset_list = [
        {
            "predict": "binanceus ETH/USDT h 5m",
            "train_on": "binanceus ETH/USDT h 5m",
        }
    ]
    d = predictoor_ss_test_dict(feedset_list=feedset_list)
    predictoor_ss = PredictoorSS(d)
    predict_feed = predictoor_ss.predict_train_feedsets[0].predict
    train_feeds = predictoor_ss.predict_train_feedsets[0].train_on
    aimodel_data_factory = AimodelDataFactory(predictoor_ss)
    mergedohlcv_df = merge_rawohlcv_dfs(ETHUSDT_RAWOHLCV_DFS)

    # =========== have testshift = 0
    target_X = np.array(
        [
            [11., 10., 9.],  # oldest
            [10., 9., 8.],
            [9., 8., 7.],
            [8., 7., 6.],
            [7., 6., 5.],
            [6., 5., 4.],
            [5., 4., 3.],
            [4., 3., 2.],  # newest
        ]
    )

    target_y = np.array(
        [
            8.,  # oldest
            7.,
            6.,
            5.,
            4.,
            3.,
            2.,
            1.,  # newest
        ]
    )
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:high:z(t-4)": [11., 10., 9., 8., 7., 6., 5., 4.],
            "binanceus:ETH/USDT:high:z(t-3)": [10., 9., 8., 7., 6., 5., 4., 3.],
            "binanceus:ETH/USDT:high:z(t-2)": [9.0, 8., 7., 6., 5., 4., 3., 2.],
        }
    )
    target_xrecent = np.array([3., 2., 1.])

    testshift = 0
    X, y, _, x_df, xrecent = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    _assert_pd_df_shape(predictoor_ss.aimodel_data_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)
    assert_array_equal(xrecent, target_xrecent)

    # =========== now, have testshift = 1
    target_X = np.array(
        [
            [12., 11., 10.],  # oldest
            [11., 10., 9.],
            [10., 9., 8.],
            [9., 8., 7.],
            [8., 7., 6.],
            [7., 6., 5.],
            [6., 5., 4.],
            [5., 4., 3.],
        ]
    )  # newest
    target_y = np.array(
        [
            9.,  # oldest
            8.,
            7.,
            6.,
            5.,
            4.,
            3.,
            2.,  # newest
        ]
    )
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:high:z(t-4)": [12., 11., 10., 9., 8., 7., 6., 5.],
            "binanceus:ETH/USDT:high:z(t-3)": [11., 10., 9., 8., 7., 6., 5., 4.],
            "binanceus:ETH/USDT:high:z(t-2)": [10., 9., 8., 7., 6., 5., 4., 3.],
        }
    )
    target_xrecent = np.array([4., 3., 2.])

    testshift = 1
    X, y, _, x_df, xrecent = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    _assert_pd_df_shape(predictoor_ss.aimodel_data_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)
    assert_array_equal(xrecent, target_xrecent)

    # =========== now have a different max_n_train
    target_X = np.array(
        [
            [9., 8., 7.],  # oldest
            [8., 7., 6.],
            [7., 6., 5.],
            [6., 5., 4.],
            [5., 4., 3.],
            [4., 3., 2.],
        ]
    )  # newest
    target_y = np.array([6., 5., 4., 3., 2., 1.])  # oldest  # newest
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:high:z(t-4)": [9., 8., 7., 6., 5., 4.],
            "binanceus:ETH/USDT:high:z(t-3)": [8., 7., 6., 5., 4., 3.],
            "binanceus:ETH/USDT:high:z(t-2)": [7., 6., 5., 4., 3., 2.],
        }
    )

    assert "max_n_train" in predictoor_ss.aimodel_data_ss.d
    predictoor_ss.aimodel_data_ss.d["max_n_train"] = 5

    testshift = 0
    X, y, _, x_df, _ = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    _assert_pd_df_shape(predictoor_ss.aimodel_data_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)


@enforce_types
def test_create_xy_notransform__2exchanges_2coins_2signals():
    # create predictoor_ss
    feedset_list = [
        {
            "predict": "binanceus ETH/USDT h 5m",
            "train_on": [
                "binanceus BTC/USDT ETH/USDT hl 5m",
                "kraken BTC/USDT ETH/USDT hl 5m",
            ],
        }
    ]
    d = predictoor_ss_test_dict(feedset_list=feedset_list)
    predictoor_ss = PredictoorSS(d)
    assert predictoor_ss.aimodel_data_ss.autoregressive_n == 3

    # create mergedohlcv_df
    rawohlcv_dfs = {
        "binanceus": {
            "BTC/USDT": _df_from_raw_data(BINANCE_BTC_DATA),
            "ETH/USDT": _df_from_raw_data(BINANCE_ETH_DATA),
        },
        "kraken": {
            "BTC/USDT": _df_from_raw_data(KRAKEN_BTC_DATA),
            "ETH/USDT": _df_from_raw_data(KRAKEN_ETH_DATA),
        },
    }
    mergedohlcv_df = merge_rawohlcv_dfs(rawohlcv_dfs)

    # create X, y, x_df
    aimodel_data_factory = AimodelDataFactory(predictoor_ss)
    testshift = 0
    predict_feed = predictoor_ss.predict_train_feedsets[0].predict
    train_feeds = predictoor_ss.predict_train_feedsets[0].train_on
    assert len(train_feeds) == 8
    X, y, _, x_df, _ = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    # test X, y, x_df
    _assert_pd_df_shape(predictoor_ss.aimodel_data_ss, X, y, x_df)
    found_cols = x_df.columns.tolist()
    target_cols = [
        "binanceus:BTC/USDT:high:z(t-4)",
        "binanceus:BTC/USDT:high:z(t-3)",
        "binanceus:BTC/USDT:high:z(t-2)",
        "binanceus:ETH/USDT:high:z(t-4)",
        "binanceus:ETH/USDT:high:z(t-3)",
        "binanceus:ETH/USDT:high:z(t-2)",
        "binanceus:BTC/USDT:low:z(t-4)",
        "binanceus:BTC/USDT:low:z(t-3)",
        "binanceus:BTC/USDT:low:z(t-2)",
        "binanceus:ETH/USDT:low:z(t-4)",
        "binanceus:ETH/USDT:low:z(t-3)",
        "binanceus:ETH/USDT:low:z(t-2)",
        "kraken:BTC/USDT:high:z(t-4)",
        "kraken:BTC/USDT:high:z(t-3)",
        "kraken:BTC/USDT:high:z(t-2)",
        "kraken:ETH/USDT:high:z(t-4)",
        "kraken:ETH/USDT:high:z(t-3)",
        "kraken:ETH/USDT:high:z(t-2)",
        "kraken:BTC/USDT:low:z(t-4)",
        "kraken:BTC/USDT:low:z(t-3)",
        "kraken:BTC/USDT:low:z(t-2)",
        "kraken:ETH/USDT:low:z(t-4)",
        "kraken:ETH/USDT:low:z(t-3)",
        "kraken:ETH/USDT:low:z(t-2)",
    ]
    assert found_cols == target_cols

    # - test binanceus:ETH/USDT:high like in 1-signal
    assert target_cols[3:6] == [
        "binanceus:ETH/USDT:high:z(t-4)",
        "binanceus:ETH/USDT:high:z(t-3)",
        "binanceus:ETH/USDT:high:z(t-2)",
    ]
    Xa = X[:, 3:6]
    assert Xa[-1, :].tolist() == [4., 3., 2.] and y[-1] == 1
    assert Xa[-2, :].tolist() == [5., 4., 3.] and y[-2] == 2
    assert Xa[0, :].tolist() == [11., 10., 9.] and y[0] == 8

    assert x_df.iloc[-1].tolist()[3:6] == [4., 3., 2.]
    assert x_df.iloc[-2].tolist()[3:6] == [5, 4., 3.]
    assert x_df.iloc[0].tolist()[3:6] == [11., 10., 9.]

    target_list = [9., 8., 7., 6., 5., 4., 3., 2.]
    assert x_df["binanceus:ETH/USDT:high:z(t-2)"].tolist() == target_list
    assert Xa[:, 2].tolist() == target_list


# ====================================================================
# utilities


@enforce_types
def _assert_pd_df_shape(
    ss: AimodelDataSS, X: np.ndarray, y: np.ndarray, x_df: pd.DataFrame
):
    assert X.shape[0] == y.shape[0]
    assert X.shape[0] == (ss.max_n_train + 1)  # 1 for test, rest for train

    assert len(x_df) == X.shape[0]
