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

SHOW_PLOT = False  # only turn on for manual testing


@enforce_types
def test_autocorrelation_SHOW_PLOT():
    """SHOW_PLOT should only be set to True temporarily in local testing."""
    assert not SHOW_PLOT


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

    y = _get_data()
    y = np.array(y)
    if do_boxcox:
        y = safe_boxcox(y)
    for _ in range(differencing_order):
        y = y[1:] - y[:-1]

    d = AutocorrelationPlotdataFactory.build(y, nlags)
    assert isinstance(d, AutocorrelationPlotdata)

    fig = plot_acf(d)
    if SHOW_PLOT:
        fig.show()

    fig = plot_pacf(d)
    if SHOW_PLOT:
        fig.show()


@enforce_types
def _get_data():
    """Return (start_ut, timeframe, yvals) for BTC 5min"""
    df = pd.read_csv(DATA_FILE)  # all data start_time = UnixTimeMs(df["timestamp"][0])
    y = df[BTC_COL].array

    return y
