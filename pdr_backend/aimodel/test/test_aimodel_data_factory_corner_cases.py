from enforce_typing import enforce_types
import polars as pl
import pytest

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.lake.merge_df import merge_rawohlcv_dfs
from pdr_backend.lake.test.resources import (
    ETHUSDT_RAWOHLCV_DFS,
    _mergedohlcv_df_ETHUSDT,
)
from pdr_backend.ppss.predictoor_ss import (
    PredictoorSS,
    predictoor_ss_test_dict,
)
from pdr_backend.util.mathutil import fill_nans, has_nan


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
    with pytest.raises(ValueError):
        factory.create_xy(
            mergedohlcv_df,
            testshift,
            predict_feed,
            do_fill_nans=False,
        )

    # nan approach 1: fix externally
    mergedohlcv_df2 = fill_nans(mergedohlcv_df)
    assert not has_nan(mergedohlcv_df2)

    # nan approach 2: explicitly tell create_xy to fill nans
    X, y, _, x_df, _ = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        do_fill_nans=True,
    )
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)

    # nan approach 3: create_xy fills nans by default (best)
    X, y, _, x_df, _ = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
    )
    assert not has_nan(X) and not has_nan(y) and not has_nan(x_df)
