from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd
import polars as pl
import pytest

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.ppss.aimodel_ss import AimodelSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict

DATA_FILE = "./pdr_backend/lake/test/merged_ohlcv_df_BTC-ETH_2024-02-01_to_2024-03-08.csv"

@enforce_types
def test_sarimax__seasonal_decomposition():
    df = pd.read_csv(DATA_FILE)
    import pdb; pdb.set_trace()

@enforce_types
def test_residuals_analysis():
    pass
    
    
@enforce_types
def test_sarimax_build_model():
    feedset_list = [
        {
            "predict": "binanceus ETH/USDT h 5m",
            "train_on": [
                "binanceus BTC/USDT ETH/USDT ohlcv 5m",
            ],
        }
    ]
    d = predictoor_ss_test_dict(feedset_list=feedset_list)
    ss = PredictoorSS(d)
    assert ss.aimodel_ss.autoregressive_n == 3

    # create mergedohlcv_df
    rawohlcv_dfs = {
        "binanceus": {
            "BTC/USDT": _df_from_raw_data(BINANCE_BTC_DATA),
            "ETH/USDT": _df_from_raw_data(BINANCE_ETH_DATA),
        },
    }
    mergedohlcv_df = merge_rawohlcv_dfs(rawohlcv_dfs)

    # create X, y, x_df
    aimodel_data_factory = AimodelDataFactory(ss)
    testshift = 0
    predict_feed = ss.predict_train_feedsets[0].predict
    train_feeds = ss.predict_train_feedsets[0].train_on
    assert len(train_feeds) == 8
    X, y, x_df, _ = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )


@enforce_types
def _assert_pd_df_shape(
    ss: AimodelSS, X: np.ndarray, y: np.ndarray, x_df: pd.DataFrame
):
    assert X.shape[0] == y.shape[0]
    assert X.shape[0] == (ss.max_n_train + 1)  # 1 for test, rest for train

    assert len(x_df) == X.shape[0]
