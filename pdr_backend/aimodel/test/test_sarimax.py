from enforce_typing import enforce_types
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
#import plotly.graph_objects as go
#from plotly.graph_objs._figure import Figure

import pytest
from statsmodels.tsa.seasonal import seasonal_decompose


from pdr_backend.util.mathutil import fill_nans, has_nan

DATA_FILE = "./pdr_backend/lake/test/merged_ohlcv_df_BTC-ETH_2024-02-01_to_2024-03-08.csv"

SHOW_PLOT = False  # only turn on for manual testing

@enforce_types
def test_sarimax_SHOW_PLOT():
    """SHOW_PLOT should only be set to True temporarily in local testing."""
    assert not SHOW_PLOT
        
# @enforce_types
# def test_residuals_analysis():
#     pass
    
    
# @enforce_types
# def test_sarimax_build_model():
#     feedset_list = [
#         {
#             "predict": "binanceus ETH/USDT h 5m",
#             "train_on": [
#                 "binanceus BTC/USDT ETH/USDT ohlcv 5m",
#             ],
#         }
#     ]
#     d = predictoor_ss_test_dict(feedset_list=feedset_list)
#     ss = PredictoorSS(d)
#     assert ss.aimodel_ss.autoregressive_n == 3

#     # create mergedohlcv_df
#     rawohlcv_dfs = {
#         "binanceus": {
#             "BTC/USDT": _df_from_raw_data(BINANCE_BTC_DATA),
#             "ETH/USDT": _df_from_raw_data(BINANCE_ETH_DATA),
#         },
#     }
#     mergedohlcv_df = merge_rawohlcv_dfs(rawohlcv_dfs)

#     # create X, y, x_df
#     aimodel_data_factory = AimodelDataFactory(ss)
#     testshift = 0
#     predict_feed = ss.predict_train_feedsets[0].predict
#     train_feeds = ss.predict_train_feedsets[0].train_on
#     assert len(train_feeds) == 8
#     X, y, x_df, _ = aimodel_data_factory.create_xy(
#         mergedohlcv_df,
#         testshift,
#         predict_feed,
#         train_feeds,
#     )
