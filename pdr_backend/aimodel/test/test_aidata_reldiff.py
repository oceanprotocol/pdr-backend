from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
import pandas as pd
import polars as pl

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.util.mathutil import has_nan
from pdr_backend.ppss.aimodel_data_ss import aimodel_data_ss_test_dict
from pdr_backend.ppss.predictoor_ss import (
    PredictoorSS,
    predictoor_ss_test_dict,
)


@enforce_types
def test_create_xy__reldiff():
    # pylint: disable=too-many-statements
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
    timestamps = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    #       t-10 t-9  t-8  t-7  t-6  t-5  t-4  t-3  t-2
    vals = [5.5, 3.0, 4.4, 3.6, 8.6, 9.7, 0.5, 0.1, 1.1]
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
    target_ytran = np.array(z_d1_rel[-5:])  # oldest to newest
    target_yraw = np.array(vals[-5:])  # ""
    assert len(target_ytran) == 4 + 1  # max_n_train + 1
    assert len(target_yraw) == 4 + 1  # ""

    ### for testshift=0, do work
    testshift = 0
    factory = AimodelDataFactory(predictoor_ss)
    predict_feed = predictoor_ss.predict_train_feedsets[0].predict
    train_feeds = predictoor_ss.predict_train_feedsets[0].train_on
    X, ytran, yraw, x_df, xrecent = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    ### for testshift=0, see results
    # all but 1 are for training, then the +1 is for testing
    assert X.shape[0] == (predictoor_ss.aimodel_data_ss.max_n_train + 1)
    assert X.shape[0] == ytran.shape[0] == yraw.shape[0]
    assert len(x_df) == X.shape[0]

    assert not has_nan(X)
    assert not has_nan(ytran) and not has_nan(yraw)
    assert not has_nan(xrecent)

    assert_allclose(X, target_X)
    assert_array_equal(ytran, target_ytran)
    assert_array_equal(yraw, target_yraw)
    assert all(x_df.columns == target_x_df.columns)
    assert_allclose(x_df.to_numpy(), target_x_df.to_numpy())
    assert str(x_df) == str(target_x_df)
    assert_allclose(xrecent, target_xrecent)

    ### for testshift=1, do work
    testshift = 1
    X2, ytran2, yraw2, x_df2, xrecent2 = factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    ### for testshift=1, see results
    # all but 1 are for training, then the +1 is for testing
    assert X2.shape[0] == (predictoor_ss.aimodel_data_ss.max_n_train + 1)
    assert X2.shape[0] == ytran2.shape[0] == yraw2.shape[0]
    assert len(x_df2) == X2.shape[0]

    assert not has_nan(X2)
    assert not has_nan(ytran2) and not has_nan(yraw2)
    assert not has_nan(xrecent2)

    assert X2[-1, 0] == X[-1 - 1, 0]
    assert ytran2[-1] == ytran[-1 - 1]
    assert yraw2[-1] == yraw[-1 - 1]
    assert all(x_df.columns == x_df2.columns)
    col0 = x_df2.columns[0]
    assert x_df2[col0][4] == x_df[col0][3]
    assert xrecent2[1] == xrecent[0]
