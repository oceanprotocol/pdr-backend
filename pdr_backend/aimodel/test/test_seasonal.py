from enforce_typing import enforce_types
import pandas as pd

from pdr_backend.aimodel.seasonal import (
    SeasonalDecomposeFactory,
    plot_seasonal,
    SeasonalPlotdata,
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
def test_seasonal_SHOW_PLOT():
    """SHOW_PLOT should only be set to True temporarily in local testing."""
    assert not SHOW_PLOT


@enforce_types
def test_relative_energy():
    (_, t, y) = _get_data()

    dr = SeasonalDecomposeFactory.build(t, y)
    es = dr.relative_energy
    assert not has_nan(es)
    assert 0 < min(es) < max(es) <= 1.0
    assert es[0] == 1.0


@enforce_types
def test_seasonal():
    (st, t, y) = _get_data()

    dr = SeasonalDecomposeFactory.build(t, y)
    assert (
        y.shape
        == dr.observed.shape
        == dr.seasonal.shape
        == dr.trend.shape
        == dr.resid.shape
    )

    plotdata = SeasonalPlotdata(st, dr)

    fig = plot_seasonal(plotdata)

    if SHOW_PLOT:
        fig.show()


@enforce_types
def _get_data():
    """Return (start_ut, timeframe, yvals) for BTC 5min"""
    df = pd.read_csv(DATA_FILE)  # all data start_time = UnixTimeMs(df["timestamp"][0])
    st = UnixTimeMs(df["timestamp"][0])
    t = ArgTimeframe("5m")
    y = df[BTC_COL].array

    return (st, t, y)
