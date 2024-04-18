from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd
import polars as pl
import pytest

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedsets
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
from pdr_backend.ppss.aimodel_ss import AimodelSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.util.mathutil import fill_nans, has_nan


@enforce_types
def test_ycont_to_ytrue():
    ycont = np.array([8.3, 6.4, 7.5, 8.6, 5.0])
    y_thr = 7.0
    target_ybool = np.array([True, False, True, True, False])

    ybool = AimodelDataFactory.ycont_to_ytrue(ycont, y_thr)
    assert_array_equal(ybool, target_ybool)


@enforce_types
def test_create_xy__0():
    # create predictoor_ss
    feedset_list = [
        {
            "predict": "binanceus ETH/USDT c 5m",
            "train_on": "binanceus ETH/USDT c 5m",
        }
    ]
    d = predictoor_ss_test_dict(feedset_list=feedset_list)
    assert "max_n_train" in d["ai_model_ss"]
    d["aimodel_ss"]["max_n_train"] = 4

    assert "autoregressive_n" in d["ai_model_ss"]
    d["aimodel_ss"]["autoregressive_n"] = 2

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
            "binanceus:ETH/USDT:open:t-3": [0.1, 0.1, 0.1, 0.1, 0.1],
            "binanceus:ETH/USDT:open:t-2": [0.1, 0.1, 0.1, 0.1, 0.1],
            "binanceus:ETH/USDT:close:t-3": [3.1, 4.2, 5.3, 6.4, 7.5],
            "binanceus:ETH/USDT:close:t-2": [4.2, 5.3, 6.4, 7.5, 8.6],
        }
    )
    target_xrecent = np.array([0.1, 0.1, 8.6, 9.7])

    target_y = np.array([5.3, 6.4, 7.5, 8.6, 9.7])  # oldest to newest

    # create X/y/etc - default train_feeds
    testshift = 0
    factory = AimodelDataFactory(predictoor_ss)
    predict_feed = predictoor_ss.predict_train_feedsets[0].predict
    X, y, x_df, xrecent = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
    )

    # test X/y/etc - default train_feeds
    _assert_pd_df_shape(predictoor_ss.aimodel_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)
    assert_array_equal(xrecent, target_xrecent)

    # create X/y/etc - explicit train_feeds
    train_feeds = predictoor_ss.predict_train_feedsets[0].train_on
    assert len(train_feeds) == 1
    X2, y2, x_df2, xrecent2 = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    # test X/y/etc - explicit train_feeds
    _assert_pd_df_shape(predictoor_ss.aimodel_ss, X2, y2, x_df2)
    assert_array_equal(X2, target_X)
    assert_array_equal(y2, target_y)
    assert x_df2.equals(target_x_df)
    assert_array_equal(xrecent2, target_xrecent)


@enforce_types
def test_create_xy_reg__1exchange_1coin_1signal():
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
            [11.0, 10.0, 9.0],  # oldest
            [10.0, 9.0, 8.0],
            [9.0, 8.0, 7.0],
            [8.0, 7.0, 6.0],
            [7.0, 6.0, 5.0],
            [6.0, 5.0, 4.0],
            [5.0, 4.0, 3.0],
            [4.0, 3.0, 2.0],  # newest
        ]
    )

    target_y = np.array(
        [
            8.0,  # oldest
            7.0,
            6.0,
            5.0,
            4.0,
            3.0,
            2.0,
            1.0,  # newest
        ]
    )
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:high:t-4": [11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0],
            "binanceus:ETH/USDT:high:t-3": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0],
            "binanceus:ETH/USDT:high:t-2": [9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0],
        }
    )
    target_xrecent = np.array([3.0, 2.0, 1.0])

    testshift = 0
    X, y, x_df, xrecent = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    _assert_pd_df_shape(predictoor_ss.aimodel_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)
    assert_array_equal(xrecent, target_xrecent)

    # =========== now, have testshift = 1
    target_X = np.array(
        [
            [12.0, 11.0, 10.0],  # oldest
            [11.0, 10.0, 9.0],
            [10.0, 9.0, 8.0],
            [9.0, 8.0, 7.0],
            [8.0, 7.0, 6.0],
            [7.0, 6.0, 5.0],
            [6.0, 5.0, 4.0],
            [5.0, 4.0, 3.0],
        ]
    )  # newest
    target_y = np.array(
        [
            9.0,  # oldest
            8.0,
            7.0,
            6.0,
            5.0,
            4.0,
            3.0,
            2.0,  # newest
        ]
    )
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:high:t-4": [12.0, 11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0],
            "binanceus:ETH/USDT:high:t-3": [11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0],
            "binanceus:ETH/USDT:high:t-2": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0],
        }
    )
    target_xrecent = np.array([4.0, 3.0, 2.0])

    testshift = 1
    X, y, x_df, xrecent = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    _assert_pd_df_shape(predictoor_ss.aimodel_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)
    assert_array_equal(xrecent, target_xrecent)

    # =========== now have a different max_n_train
    target_X = np.array(
        [
            [9.0, 8.0, 7.0],  # oldest
            [8.0, 7.0, 6.0],
            [7.0, 6.0, 5.0],
            [6.0, 5.0, 4.0],
            [5.0, 4.0, 3.0],
            [4.0, 3.0, 2.0],
        ]
    )  # newest
    target_y = np.array([6.0, 5.0, 4.0, 3.0, 2.0, 1.0])  # oldest  # newest
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:high:t-4": [9.0, 8.0, 7.0, 6.0, 5.0, 4.0],
            "binanceus:ETH/USDT:high:t-3": [8.0, 7.0, 6.0, 5.0, 4.0, 3.0],
            "binanceus:ETH/USDT:high:t-2": [7.0, 6.0, 5.0, 4.0, 3.0, 2.0],
        }
    )

    assert "max_n_train" in predictoor_ss.aimodel_ss.d
    predictoor_ss.aimodel_ss.d["max_n_train"] = 5

    testshift = 0
    X, y, x_df, _ = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    _assert_pd_df_shape(predictoor_ss.aimodel_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)


@enforce_types
def test_create_xy_reg__2exchanges_2coins_2signals():

    # create predictoor_ss
    d = predictoor_ss_test_dict()
    feedsets = PredictTrainFeedsets.from_array(
        [
            {
                "predict": "binanceus ETH/USDT h 5m",
                "train_on": [
                    "binanceus BTC/USDT ETH/USDT h 5m",
                    "kraken BTC/USDT ETH/USDT h 5m",
                ],
            }
        ]
    )
    assert "predict_train_feedsets" in d
    d["predict_train_feedsets"] = feedsets
    ss = PredictoorSS(d)
    assert ss.aimodel_ss.autoregressive_n == 3

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
    aimodel_data_factory = AimodelDataFactory(ss)
    testshift = 0
    predict_feed = ss.predict_train_feedsets[0].predict
    train_feeds = ss.predict_train_feedsets[0].train_on
    assert len(train_feeds) == 4
    X, y, x_df, _ = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    # test X, y, x_df
    _assert_pd_df_shape(ss.aimodel_ss, X, y, x_df)
    found_cols = x_df.columns.tolist()
    target_cols = [
        "binanceus:BTC/USDT:high:t-4",
        "binanceus:BTC/USDT:high:t-3",
        "binanceus:BTC/USDT:high:t-2",
        "binanceus:ETH/USDT:high:t-4",
        "binanceus:ETH/USDT:high:t-3",
        "binanceus:ETH/USDT:high:t-2",
        "binanceus:BTC/USDT:low:t-4",
        "binanceus:BTC/USDT:low:t-3",
        "binanceus:BTC/USDT:low:t-2",
        "binanceus:ETH/USDT:low:t-4",
        "binanceus:ETH/USDT:low:t-3",
        "binanceus:ETH/USDT:low:t-2",
        "kraken:BTC/USDT:high:t-4",
        "kraken:BTC/USDT:high:t-3",
        "kraken:BTC/USDT:high:t-2",
        "kraken:ETH/USDT:high:t-4",
        "kraken:ETH/USDT:high:t-3",
        "kraken:ETH/USDT:high:t-2",
        "kraken:BTC/USDT:low:t-4",
        "kraken:BTC/USDT:low:t-3",
        "kraken:BTC/USDT:low:t-2",
        "kraken:ETH/USDT:low:t-4",
        "kraken:ETH/USDT:low:t-3",
        "kraken:ETH/USDT:low:t-2",
    ]
    assert found_cols == target_cols

    # - test binanceus:ETH/USDT:high like in 1-signal
    assert target_cols[3:6] == [
        "binanceus:ETH/USDT:high:t-4",
        "binanceus:ETH/USDT:high:t-3",
        "binanceus:ETH/USDT:high:t-2",
    ]
    Xa = X[:, 3:6]
    assert Xa[-1, :].tolist() == [4.0, 3.0, 2.0] and y[-1] == 1
    assert Xa[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
    assert Xa[0, :].tolist() == [11, 10, 9] and y[0] == 8

    assert x_df.iloc[-1].tolist()[3:6] == [4, 3, 2]
    assert x_df.iloc[-2].tolist()[3:6] == [5, 4, 3]
    assert x_df.iloc[0].tolist()[3:6] == [11, 10, 9]

    target_list = [9, 8, 7, 6, 5, 4, 3, 2]
    assert x_df["binanceus:ETH/USDT:high:t-2"].tolist() == target_list
    assert Xa[:, 2].tolist() == target_list


@enforce_types
def test_create_xy_reg__check_timestamp_order():
    mergedohlcv_df, factory = _mergedohlcv_df_ETHUSDT()

    # timestamps should be descending order
    uts = mergedohlcv_df["timestamp"].to_list()
    assert uts == sorted(uts, reverse=False)

    # happy path
    testshift = 0
    predict_feed = factory.ss.predict_train_feedsets[0].predict
    factory.create_xy(mergedohlcv_df, testshift, predict_feed)

    # failure path
    bad_uts = sorted(uts, reverse=True)  # bad order
    bad_mergedohlcv_df = mergedohlcv_df.with_columns(pl.Series("timestamp", bad_uts))
    with pytest.raises(AssertionError):
        factory.create_xy(bad_mergedohlcv_df, testshift, predict_feed)


@enforce_types
def test_create_xy_reg__input_type():
    mergedohlcv_df, factory = _mergedohlcv_df_ETHUSDT()

    assert isinstance(mergedohlcv_df, pl.DataFrame)
    assert isinstance(factory, AimodelDataFactory)

    # create_xy() input should be pl
    testshift = 0
    predict_feed = factory.ss.predict_train_feedsets[0].predict
    factory.create_xy(mergedohlcv_df, testshift, predict_feed)

    # create_xy() inputs shouldn't be pd
    pandas_df = mergedohlcv_df.to_pandas()
    with pytest.raises(AssertionError):
        factory.create_xy(pandas_df, testshift, predict_feed)


@enforce_types
def test_create_xy_reg__handle_nan():
    # create mergedohlcv_df
    feeds = [
        {
            "predict": "binanceus ETH/USDT h 5m",
            "train_on": "binanceus ETH/USDT h 5m",
        }
    ]
    d = predictoor_ss_test_dict(feedset_list=feeds)
    predictoor_ss = PredictoorSS(d)
    predict_feed = predictoor_ss.predict_train_feedsets[0].predict
    testshift = 0
    factory = AimodelDataFactory(predictoor_ss)
    mergedohlcv_df = merge_rawohlcv_dfs(ETHUSDT_RAWOHLCV_DFS)

    # initial mergedohlcv_df should be ok
    assert not has_nan(mergedohlcv_df)

    # now, corrupt mergedohlcv_df with NaN values
    nan_indices = [1686805800000, 1686806700000, 1686808800000]
    mergedohlcv_df = mergedohlcv_df.with_columns(
        [
            pl.when(mergedohlcv_df["timestamp"].is_in(nan_indices))
            .then(pl.lit(None, pl.Float64))
            .otherwise(mergedohlcv_df["binanceus:ETH/USDT:high"])
            .alias("binanceus:ETH/USDT:high")
        ]
    )
    assert has_nan(mergedohlcv_df)

    # run create_xy() and force the nans to stick around
    # -> we want to ensure that we're building X/y with risk of nan
    X, y, x_df, _ = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        do_fill_nans=False,
    )
    assert has_nan(X) and has_nan(y) and has_nan(x_df)

    # nan approach 1: fix externally
    mergedohlcv_df2 = fill_nans(mergedohlcv_df)
    assert not has_nan(mergedohlcv_df2)

    # nan approach 2: explicitly tell create_xy to fill nans
    X, y, x_df, _ = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        do_fill_nans=True,
    )
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)

    # nan approach 3: create_xy fills nans by default (best)
    X, y, x_df, _ = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
    )
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)


# ====================================================================
# utilities


@enforce_types
def _assert_pd_df_shape(
    ss: AimodelSS, X: np.ndarray, y: np.ndarray, x_df: pd.DataFrame
):
    assert X.shape[0] == y.shape[0]
    assert X.shape[0] == (ss.max_n_train + 1)  # 1 for test, rest for train
    assert X.shape[1] == ss.n

    assert len(x_df) == X.shape[0]
    assert len(x_df.columns) == ss.n
