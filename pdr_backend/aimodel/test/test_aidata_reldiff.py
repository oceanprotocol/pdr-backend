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
def test_create_xy__reldiff():
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
            autoregressive_n=2,
            transform="RelDiff",
        ),
    )
    predictoor_ss = PredictoorSS(d)

    # create df
    timestamps = [1, 2, 3, 4, 5, 6, 7, 8]
    #       t-9  t-8  t-7  t-6  t-5  t-4  t-3  t-2
    vals = [3.0, 4.4, 3.6, 8.6, 9.7, 0.5, 0.1, 1.1]
    mergedohlcv_df = pl.DataFrame(
        {
            # every column is ordered from youngest to oldest
            "timestamp": timestamps,  # not used by AimodelDataFactory
            "binanceus:ETH/USDT:close": vals,
        }
    )

    # set z_d1_rel -- the main data
    z_d1_abs = np.array(vals[1:]) - np.array(vals[:-1])
    z_d1_rel = z_d1_abs / np.array(vals[:-1])
    assert z_d1_abs[-1] == 1.1 - 0.1
    assert z_d1_rel[-1] == (1.1 - 0.1) / (0.1)

    # set target X,y
    target_x_df = pd.DataFrame(
        {
            "binanceus:ETH/USDT:close:(z(t-3)-z(t-4))/z(t-4)": z_d1_rel[-7:-2],
            "binanceus:ETH/USDT:close:(z(t-2)-z(t-3))/z(t-3)": z_d1_rel[-6:-1],
        }
    )
    target_X = target_x_df.to_numpy()
    assert target_X.shape == (4 + 1, 2)  # (max_n_train + 1, num_cols)

    target_xrecent = np.array(z_d1_rel[-2:])
    target_y = np.array(z_d1_rel[-5:])  # oldest to newest
    assert len(target_y) == 4 + 1  # max_n_train + 1

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

    # do work
    testshift = 1
    X2, y2, _, x_df2, xrecent2 = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )
    assert X2[-1, 0] == X[-1 - 1, 0]
    assert y2[-1] == y[-1 - 1]
    assert all(x_df.columns == x_df2.columns)
    col0 = x_df.columns[0]
    assert x_df2[col0][3] == x_df[col0][3]
    assert xrecent2[1] == xrecent[0]
