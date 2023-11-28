from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import polars as pl
import pytest

from pdr_backend.data_eng.model_data_factory import ModelDataFactory
from pdr_backend.data_eng.parquet_data_factory import ParquetDataFactory
from pdr_backend.data_eng.test.resources import (
    _data_pp_ss_1feed,
    _data_pp,
    _data_ss,
    _df_from_raw_data,
    BINANCE_ETH_DATA,
    BINANCE_BTC_DATA,
    KRAKEN_ETH_DATA,
    KRAKEN_BTC_DATA,
    ETHUSDT_PARQUET_DFS,
)
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.util.mathutil import has_nan, fill_nans


@enforce_types
def test_create_xy__1exchange_1coin_1signal(tmpdir):
    _, ss, pq_data_factory, model_data_factory = _data_pp_ss_1feed(
        tmpdir, "binanceus h ETH-USDT"
    )
    hist_df = pq_data_factory._merge_parquet_dfs(ETHUSDT_PARQUET_DFS)

    # =========== initial testshift (0)
    X, y, x_df = model_data_factory.create_xy(hist_df, testshift=0)
    _assert_pd_df_shape(ss, X, y, x_df)

    assert X[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
    assert X[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
    assert X[0, :].tolist() == [11, 10, 9] and y[0] == 8

    assert x_df.iloc[-1].tolist() == [4, 3, 2]

    found_cols = x_df.columns.tolist()
    target_cols = [
        "binanceus:ETH-USDT:high:t-4",
        "binanceus:ETH-USDT:high:t-3",
        "binanceus:ETH-USDT:high:t-2",
    ]
    assert found_cols == target_cols

    assert x_df["binanceus:ETH-USDT:high:t-2"].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]
    assert X[:, 2].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]

    # =========== now have a different testshift (1 not 0)
    X, y, x_df = model_data_factory.create_xy(hist_df, testshift=1)
    _assert_pd_df_shape(ss, X, y, x_df)

    assert X[-1, :].tolist() == [5, 4, 3] and y[-1] == 2
    assert X[-2, :].tolist() == [6, 5, 4] and y[-2] == 3
    assert X[0, :].tolist() == [12, 11, 10] and y[0] == 9

    assert x_df.iloc[-1].tolist() == [5, 4, 3]

    found_cols = x_df.columns.tolist()
    target_cols = [
        "binanceus:ETH-USDT:high:t-4",
        "binanceus:ETH-USDT:high:t-3",
        "binanceus:ETH-USDT:high:t-2",
    ]
    assert found_cols == target_cols

    assert x_df["binanceus:ETH-USDT:high:t-2"].tolist() == [10, 9, 8, 7, 6, 5, 4, 3]
    assert X[:, 2].tolist() == [10, 9, 8, 7, 6, 5, 4, 3]

    # =========== now have a different max_n_train
    ss.d["max_n_train"] = 5

    X, y, x_df = model_data_factory.create_xy(hist_df, testshift=0)
    _assert_pd_df_shape(ss, X, y, x_df)

    assert X.shape[0] == 5 + 1  # +1 for one test point
    assert y.shape[0] == 5 + 1
    assert len(x_df) == 5 + 1

    assert X[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
    assert X[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
    assert X[0, :].tolist() == [9, 8, 7] and y[0] == 6


@enforce_types
def test_create_xy__2exchanges_2coins_2signals(tmpdir):
    parquet_dir = str(tmpdir)

    parquet_dfs = {
        "binanceus": {
            "BTC-USDT": _df_from_raw_data(BINANCE_BTC_DATA),
            "ETH-USDT": _df_from_raw_data(BINANCE_ETH_DATA),
        },
        "kraken": {
            "BTC-USDT": _df_from_raw_data(KRAKEN_BTC_DATA),
            "ETH-USDT": _df_from_raw_data(KRAKEN_ETH_DATA),
        },
    }

    pp = _data_pp(["binanceus h ETH-USDT"])
    ss = _data_ss(
        parquet_dir,
        ["binanceus hl BTC-USDT,ETH-USDT", "kraken hl BTC-USDT,ETH-USDT"],
    )
    assert ss.autoregressive_n == 3
    assert ss.n == (4 + 4) * 3

    pq_data_factory = ParquetDataFactory(pp, ss)
    hist_df = pq_data_factory._merge_parquet_dfs(parquet_dfs)

    model_data_factory = ModelDataFactory(pp, ss)
    X, y, x_df = model_data_factory.create_xy(hist_df, testshift=0)
    _assert_pd_df_shape(ss, X, y, x_df)

    found_cols = x_df.columns.tolist()
    target_cols = [
        "binanceus:BTC-USDT:high:t-4",
        "binanceus:BTC-USDT:high:t-3",
        "binanceus:BTC-USDT:high:t-2",
        "binanceus:ETH-USDT:high:t-4",
        "binanceus:ETH-USDT:high:t-3",
        "binanceus:ETH-USDT:high:t-2",
        "binanceus:BTC-USDT:low:t-4",
        "binanceus:BTC-USDT:low:t-3",
        "binanceus:BTC-USDT:low:t-2",
        "binanceus:ETH-USDT:low:t-4",
        "binanceus:ETH-USDT:low:t-3",
        "binanceus:ETH-USDT:low:t-2",
        "kraken:BTC-USDT:high:t-4",
        "kraken:BTC-USDT:high:t-3",
        "kraken:BTC-USDT:high:t-2",
        "kraken:ETH-USDT:high:t-4",
        "kraken:ETH-USDT:high:t-3",
        "kraken:ETH-USDT:high:t-2",
        "kraken:BTC-USDT:low:t-4",
        "kraken:BTC-USDT:low:t-3",
        "kraken:BTC-USDT:low:t-2",
        "kraken:ETH-USDT:low:t-4",
        "kraken:ETH-USDT:low:t-3",
        "kraken:ETH-USDT:low:t-2",
    ]
    assert found_cols == target_cols

    # test binanceus:ETH-USDT:high like in 1-signal
    assert target_cols[3:6] == [
        "binanceus:ETH-USDT:high:t-4",
        "binanceus:ETH-USDT:high:t-3",
        "binanceus:ETH-USDT:high:t-2",
    ]
    Xa = X[:, 3:6]
    assert Xa[-1, :].tolist() == [4, 3, 2] and y[-1] == 1
    assert Xa[-2, :].tolist() == [5, 4, 3] and y[-2] == 2
    assert Xa[0, :].tolist() == [11, 10, 9] and y[0] == 8

    assert x_df.iloc[-1].tolist()[3:6] == [4, 3, 2]
    assert x_df.iloc[-2].tolist()[3:6] == [5, 4, 3]
    assert x_df.iloc[0].tolist()[3:6] == [11, 10, 9]

    assert x_df["binanceus:ETH-USDT:high:t-2"].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]
    assert Xa[:, 2].tolist() == [9, 8, 7, 6, 5, 4, 3, 2]


@enforce_types
def test_create_xy__input_type(tmpdir):
    # hist_df should be pl
    _, _, pq_data_factory, model_data_factory = _data_pp_ss_1feed(
        tmpdir, "binanceus h ETH-USDT"
    )
    assert isinstance(model_data_factory, ModelDataFactory)
    hist_df = pq_data_factory._merge_parquet_dfs(ETHUSDT_PARQUET_DFS)
    assert isinstance(hist_df, pl.DataFrame)

    # create_xy() input should be pl
    model_data_factory.create_xy(hist_df, testshift=0)

    # create_xy() inputs shouldn't be pd
    with pytest.raises(AssertionError):
        model_data_factory.create_xy(hist_df.to_pandas(), testshift=0)


@enforce_types
def test_create_xy__handle_nan(tmpdir):
    # create hist_df
    __, __, pq_data_factory, model_data_factory = _data_pp_ss_1feed(
        tmpdir, "binanceus h ETH-USDT"
    )
    hist_df = pq_data_factory._merge_parquet_dfs(ETHUSDT_PARQUET_DFS)

    # initial hist_df should be ok
    assert not has_nan(hist_df)

    # now, corrupt hist_df with NaN values
    nan_indices = [1686805800000, 1686806700000, 1686808800000]
    hist_df = hist_df.with_columns(
        [
            pl.when(hist_df["timestamp"].is_in(nan_indices))
            .then(pl.lit(None, pl.Float64))
            .otherwise(hist_df["binanceus:ETH-USDT:high"])
            .alias("binanceus:ETH-USDT:high")
        ]
    )
    assert has_nan(hist_df)

    # =========== initial testshift (0)
    # run create_xy() and force the nans to stick around
    # -> we want to ensure that we're building X/y with risk of nan
    X, y, x_df = model_data_factory.create_xy(hist_df, testshift=0, do_fill_nans=False)
    assert has_nan(X) and has_nan(y) and has_nan(x_df)

    # nan approach 1: fix externally
    hist_df2 = fill_nans(hist_df)
    assert not has_nan(hist_df2)

    # nan approach 2: explicitly tell create_xy to fill nans
    X, y, x_df = model_data_factory.create_xy(hist_df, testshift=0, do_fill_nans=True)
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)

    # nan approach 3: create_xy fills nans by default (best)
    X, y, x_df = model_data_factory.create_xy(hist_df, testshift=0)
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)


# ====================================================================
# utilities


@enforce_types
def _assert_pd_df_shape(ss: DataSS, X: np.ndarray, y: np.ndarray, x_df: pd.DataFrame):
    assert X.shape[0] == y.shape[0]
    assert X.shape[0] == (ss.max_n_train + 1)  # 1 for test, rest for train
    assert X.shape[1] == ss.n

    assert len(x_df) == X.shape[0]
    assert len(x_df.columns) == ss.n
