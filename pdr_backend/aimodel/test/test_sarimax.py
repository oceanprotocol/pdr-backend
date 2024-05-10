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

    
@enforce_types
def test_sarimax__seasonal_decomposition():
    col_s = "binance:BTC/USDT:close"
    df = pd.read_csv(DATA_FILE) # all data
    import pdb; pdb.set_trace()

    y = df[col_s].array
    period = 288 # 288 5min epochs per day. https://stackoverflow.com/questions/60017052/decompose-for-time-series-valueerror-you-must-specify-a-period-or-x-must-be
    decompose_result = seasonal_decompose(y, period=period) # class DecomposeResult

    if False:
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("datetime")
        df = pd.concat([df[col_s]]) # just BTC/USDT c column
        df = df.asfreq(freq='5min')
        #if has_nan(df):
        #    df = fill_nans(df)
        decompose_result = seasonal_decompose(df) # class DecomposeResult


        # https://www.statsmodels.org/dev/generated/statsmodels.tsa.seasonal.DecomposeResult.html#statsmodels.tsa.seasonal.DecomposeResult

        # x must be a pandas object with a DatetimeIndex with a freq not set to None
        decompose_result = seasonal_decompose(df) # class DecomposeResult

    #decompose_plot = decompose_result.plot()
    decompose_result.plot()
    
    #figure = go.Figure()
    #figure.add_trace(decompose_plot)
    if SHOW_PLOT:
        plt.show()
        #figure.show()


    import pdb; pdb.set_trace()
        
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
