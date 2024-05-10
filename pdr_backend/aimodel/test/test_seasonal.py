from enforce_typing import enforce_types
import numpy as np
import pandas as pd

import plotly.graph_objects as go
from plotly.graph_objs._figure import Figure

import pytest

from pdr_backend.aimodel.seasonal import (
    pdr_seasonal_decompose,
    plot_seasonal,
    SeasonalPlotdata,
)
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.util.time_types import UnixTimeMs


DATA_FILE = "./pdr_backend/lake/test/merged_ohlcv_df_BTC-ETH_2024-02-01_to_2024-03-08.csv"
BTC_COL = "binance:BTC/USDT:close"

SHOW_PLOT = True  # only turn on for manual testing


@enforce_types
def test_seasonal_SHOW_PLOT():
    """SHOW_PLOT should only be set to True temporarily in local testing."""
    assert not SHOW_PLOT


@enforce_types
def test_seasonal():
    df = pd.read_csv(DATA_FILE) # all data start_time = UnixTimeMs(df["timestamp"][0])
    st = UnixTimeMs(df["timestamp"][0])
    t = ArgTimeframe("5m")
    y = df[BTC_COL].array
    
    dr = pdr_seasonal_decompose(t, y)
    assert y.shape == dr.observed.shape == dr.seasonal.shape \
        == dr.trend.shape == dr.resid.shape

    plotdata = SeasonalPlotdata(st, t, dr)

    fig = plot_seasonal(plotdata)
    
    if SHOW_PLOT:
        fig.show()
    
