from enforce_typing import enforce_types
import pandas as pd
from scipy import stats     

from pdr_backend.aimodel.autocorrelation import (
    AutocorrelationPlotdata,
    AutocorrelationPlotdataFactory,
    plot_autocorrelation,
)
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.util.mathutil import has_nan
from pdr_backend.util.time_types import UnixTimeMs

DATA_FILE = (
    "./pdr_backend/lake/test/merged_ohlcv_df_BTC-ETH_2024-02-01_to_2024-03-08.csv"
)
BTC_COL = "binance:BTC/USDT:close"

SHOW_PLOT = True  # only turn on for manual testing


@enforce_types
def test_autocorrelation_SHOW_PLOT():
    """SHOW_PLOT should only be set to True temporarily in local testing."""
    assert not SHOW_PLOT


@enforce_types
def test_autocorrelation():
    # play with me
    nlags = 20
    do_boxcox = True
    differencing_order = 0

    # 
    y = _get_data()
    if do_boxcox:
        y, _ = stats.boxcox(y)
    for i in range(differencing_order):
        y = y[1:] - y[:-1]
        
    d = AutocorrelationPlotdataFactory.build(y, nlags)
    assert isinstance(d, AutocorrelationPlotdata)
    assert (
        d.acf_results.max_lag
        == len(d.acf_results.values)
        == len(d.acf_results.lower_values)
        == len(d.acf_results.upper_values)
        == d.pacf_results.max_lag
        == len(d.pacf_results.values)
        == len(d.pacf_results.lower_values)
        == len(d.pacf_results.upper_values)
    )
    
    fig = plot_autocorrelation(d)

    if SHOW_PLOT:
        fig.show()


@enforce_types
def _get_data():
    """Return (start_ut, timeframe, yvals) for BTC 5min"""
    df = pd.read_csv(DATA_FILE)  # all data start_time = UnixTimeMs(df["timestamp"][0])
    y = df[BTC_COL].array

    return y
