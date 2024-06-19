import os
from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import pytest

from pdr_backend.statutil.autocorrelation_plotdata import (
    AutocorrelationPlotdata,
    AutocorrelationPlotdataFactory,
)
from pdr_backend.statutil.autocorrelation_plotter import plot_acf, plot_pacf
from pdr_backend.statutil.boxcox import safe_boxcox

DATA_FILE = (
    "./pdr_backend/lake/test/merged_ohlcv_df_BTC-ETH_2024-02-01_to_2024-03-08.csv"
)
BTC_COL = "binance:BTC/USDT:close"

# set env variable as true to show plots
SHOW_PLOT = os.getenv("SHOW_PLOT", "false").lower() == "true"


@enforce_types
@pytest.mark.parametrize(
    "do_boxcox, differencing_order",
    [
        (False, 0),
        (True, 0),
        (True, 1),
        (True, 2),
    ],
)
def test_autocorrelation(do_boxcox, differencing_order):
    nlags = 5  # play with me

    x = _get_data()
    x = np.array(x)
    if do_boxcox:
        x = safe_boxcox(x)
    for _ in range(differencing_order):
        x = x[1:] - x[:-1]

    d = AutocorrelationPlotdataFactory.build(x, nlags)
    assert isinstance(d, AutocorrelationPlotdata)

    fig = plot_acf(d)
    if SHOW_PLOT:
        fig.show()

    fig = plot_pacf(d)
    if SHOW_PLOT:
        fig.show()


@enforce_types
def _get_data():
    """Return (start_ut, timeframe, xvals) for BTC 5min"""
    df = pd.read_csv(DATA_FILE)  # all data start_time = UnixTimeMs(df["timestamp"][0])
    x = df[BTC_COL].array

    return x
