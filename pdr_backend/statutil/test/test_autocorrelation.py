from enforce_typing import enforce_types
import numpy as np
import pandas as pd

from pdr_backend.statutil.autocorrelation import (
    AutocorrelationPlotdata,
    AutocorrelationPlotdataFactory,
    plot_autocorrelation,
)
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
def test_autocorrelation():
    # play with me
    nlags = 5
    do_boxcox = True
    differencing_order = 1

    #
    y = np.array(_get_data())  # [:1000]
    if do_boxcox:
        y = safe_boxcox(y)
    for _ in range(differencing_order):
        y = y[1:] - y[:-1]

    d = AutocorrelationPlotdataFactory.build(y, nlags)
    assert isinstance(d, AutocorrelationPlotdata)

    fig = plot_autocorrelation(d)

    if SHOW_PLOT:
        fig.show()


@enforce_types
def _get_data():
    """Return (start_ut, timeframe, yvals) for BTC 5min"""
    df = pd.read_csv(DATA_FILE)  # all data start_time = UnixTimeMs(df["timestamp"][0])
    y = df[BTC_COL].array

    return y
