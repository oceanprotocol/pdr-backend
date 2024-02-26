import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd
import polars as pl
import pytest
from enforce_typing import enforce_types

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
from pdr_backend.ppss.aimodel_ss import AimodelSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.util.mathutil import fill_nans, has_nan


@enforce_types
def test_ycont_to_ytrue(tmpdir):
    ycont = np.array([8.3, 6.4, 7.5, 8.6, 5.0])
    y_thr = 7.0
    target_ybool = np.array([True, False, True, True, False])

    ybool = AimodelDataFactory.ycont_to_ytrue(ycont, y_thr)
    assert_array_equal(ybool, target_ybool)


@enforce_types
def test_create_xy__0():
    predictoor_ss = PredictoorSS(
        {
            "predict_feed": "binanceus ETH/USDT c 5m",
            "approach": 1,
            "stake_amount": 1,
            "bot_only": {
                "s_until_epoch_end": 60,
            },
            "sim_only": {
                "others_stake": 3,
                "others_accuracy": 0.51,
                "revenue": 0.93,
            },
            "aimodel_ss": {
                "input_feeds": ["binanceus ETH/USDT oc"],
                "approach": "LinearLogistic",
                "max_n_train": 4,
                "autoregressive_n": 2,
            },
        }
    )
    mergedohlcv_df = pl.DataFrame(
        {
            # every column is ordered from youngest to oldest
            "timestamp": [1, 2, 3, 4, 5, 6, 7, 8],  # not used by AimodelDataFactory
            # The underlying AR process is: close[t] = close[t-1] + open[t-1]
            "binanceus:ETH/USDT:open": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            "binanceus:ETH/USDT:close": [2.0, 3.1, 4.2, 5.3, 6.4, 7.5, 8.6, 9.7],
        }
    )

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

    factory = AimodelDataFactory(predictoor_ss)

    target_y = np.array([5.3, 6.4, 7.5, 8.6, 9.7])  # oldest to newest
    X, y, x_df, xrecent = factory.create_xy(mergedohlcv_df, testshift=0)
    _assert_pd_df_shape(predictoor_ss.aimodel_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)
    assert_array_equal(xrecent, target_xrecent)


@enforce_types
def test_create_xy_reg__1exchange_1coin_1signal(tmpdir):
    d = predictoor_ss_test_dict("binanceus ETH/USDT h 5m")
    ss = PredictoorSS(d)
    aimodel_data_factory = AimodelDataFactory(ss)
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

    X, y, x_df, xrecent = aimodel_data_factory.create_xy(mergedohlcv_df, testshift=0)

    _assert_pd_df_shape(ss.aimodel_ss, X, y, x_df)
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

    X, y, x_df, xrecent = aimodel_data_factory.create_xy(mergedohlcv_df, testshift=1)

    _assert_pd_df_shape(ss.aimodel_ss, X, y, x_df)
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

    assert "max_n_train" in ss.aimodel_ss.d
    ss.aimodel_ss.d["max_n_train"] = 5

    X, y, x_df, _ = aimodel_data_factory.create_xy(mergedohlcv_df, testshift=0)

    _assert_pd_df_shape(ss.aimodel_ss, X, y, x_df)
    assert_array_equal(X, target_X)
    assert_array_equal(y, target_y)
    assert x_df.equals(target_x_df)


@enforce_types
def test_create_xy_reg__2exchanges_2coins_2signals():
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

    d = predictoor_ss_test_dict()
    assert "predict_feed" in d
    assert "input_feeds" in d["aimodel"]
    d["predict_feed"] = "binanceus ETH/USDT h 5m"
    d["aimodel_ss"]["input_feeds"] = [
        "binanceus BTC/USDT,ETH/USDT hl",
        "kraken BTC/USDT,ETH/USDT hl",
    ]
    ss = PredictoorSS(d)

    assert ss.aimodel_ss.autoregressive_n == 3
    assert ss.aimodel_ss.n == (4 + 4) * 3

    mergedohlcv_df = merge_rawohlcv_dfs(rawohlcv_dfs)

    aimodel_data_factory = AimodelDataFactory(ss)
    X, y, x_df, _ = aimodel_data_factory.create_xy(mergedohlcv_df, testshift=0)

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

    # test binanceus:ETH/USDT:high like in 1-signal
    assert target_cols[3:6] == [
        "binanceus:ETH/USDT:high:t-4",
        "binanceus:ETH/USDT:high:t-3",
        "binanceus:ETH/USDT:high:t-2",
    ]
    Xa = X[:, 3:6]
    assert Xa[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
    assert Xa[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
    assert Xa[0, :].tolist() == [11, 10, 9] and y[0] == 8

    assert x_df.iloc[-1].tolist()[3:6] == [4, 3, 2]
    assert x_df.iloc[-2].tolist()[3:6] == [5, 4, 3]
    assert x_df.iloc[0].tolist()[3:6] == [11, 10, 9]

    assert x_df["binanceus:ETH/USDT:high:t-2"].tolist() == [
        9,
        8,
        7,
        6,
        5,
        4,
        3,
        2,
    ]
    assert Xa[:, 2].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]


@enforce_types
def test_create_xy_reg__check_timestamp_order(tmpdir):
    mergedohlcv_df, factory = _mergedohlcv_df_ETHUSDT(tmpdir)

    # timestamps should be descending order
    uts = mergedohlcv_df["timestamp"].to_list()
    assert uts == sorted(uts, reverse=False)

    # happy path
    factory.create_xy(mergedohlcv_df, testshift=0)

    # failure path
    bad_uts = sorted(uts, reverse=True)  # bad order
    bad_mergedohlcv_df = mergedohlcv_df.with_columns(pl.Series("timestamp", bad_uts))
    with pytest.raises(AssertionError):
        factory.create_xy(bad_mergedohlcv_df, testshift=0)


@enforce_types
def test_create_xy_reg__input_type(tmpdir):
    mergedohlcv_df, aimodel_data_factory = _mergedohlcv_df_ETHUSDT(tmpdir)

    assert isinstance(mergedohlcv_df, pl.DataFrame)
    assert isinstance(aimodel_data_factory, AimodelDataFactory)

    # create_xy() input should be pl
    aimodel_data_factory.create_xy(mergedohlcv_df, testshift=0)

    # create_xy() inputs shouldn't be pd
    with pytest.raises(AssertionError):
        aimodel_data_factory.create_xy(mergedohlcv_df.to_pandas(), testshift=0)


@enforce_types
def test_create_xy_reg__handle_nan(tmpdir):
    # create mergedohlcv_df
    d = predictoor_ss_test_dict("binanceus ETH/USDT h 5m")
    ss = PredictoorSS(d)
    aimodel_data_factory = AimodelDataFactory(ss)
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

    # =========== initial testshift (0)
    # run create_xy() and force the nans to stick around
    # -> we want to ensure that we're building X/y with risk of nan
    X, y, x_df, _ = aimodel_data_factory.create_xy(
        mergedohlcv_df, testshift=0, do_fill_nans=False
    )
    assert has_nan(X) and has_nan(y) and has_nan(x_df)

    # nan approach 1: fix externally
    mergedohlcv_df2 = fill_nans(mergedohlcv_df)
    assert not has_nan(mergedohlcv_df2)

    # nan approach 2: explicitly tell create_xy to fill nans
    X, y, x_df, _ = aimodel_data_factory.create_xy(
        mergedohlcv_df, testshift=0, do_fill_nans=True
    )
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)

    # nan approach 3: create_xy fills nans by default (best)
    X, y, x_df, _ = aimodel_data_factory.create_xy(mergedohlcv_df, testshift=0)
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
