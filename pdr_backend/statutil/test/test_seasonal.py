import os
import shutil

import pandas as pd
from dash import Dash
from enforce_typing import enforce_types

from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.statutil.dash_plots.callbacks import get_callbacks
from pdr_backend.statutil.dash_plots.view_elements import get_layout
from pdr_backend.statutil.seasonal import (
    SeasonalDecomposeFactory,
    SeasonalPlotdata,
    plot_seasonal,
)
from pdr_backend.util.mathutil import has_nan
from pdr_backend.util.time_types import UnixTimeMs

DATA_FILE = (
    "./pdr_backend/lake/test/merged_ohlcv_df_BTC-ETH_2024-02-01_to_2024-03-08.csv"
)
BTC_COL = "binance:BTC/USDT:close"

# set env variable as true to show plots
SHOW_PLOT = os.getenv("SHOW_PLOT", "false").lower() == "true"


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
# pylint: disable=unused-argument
def test_empty_dashboard(tmpdir, check_chromedriver, dash_duo):
    app = Dash("pdr_backend.statutil.arima_dash")
    app.config["suppress_callback_exceptions"] = True
    app.layout = get_layout()
    app.layout.children[0].data = str(tmpdir)
    get_callbacks(app)

    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal(
        "#error-message h2",
        "No data found! Fetch ohlcv data before running the ARIMA plots.",
    )


@enforce_types
# pylint: disable=unused-argument
def test_dashboard(tmpdir, check_chromedriver, dash_duo):
    test_dir = str(tmpdir)

    # Sample Parquet files
    """
    src = os.path.join(
        os.path.dirname(__file__), "../../tests/resources/binance_ETH-USDT_5m.parquet"
    )
    shutil.copyfile(src, test_dir + "/binance_ETH-USDT_5m.parquet")
    """

    src = os.path.join(
        os.path.dirname(__file__), "../../tests/resources/binance_ETH-USDT_5m.parquet"
    )
    shutil.copyfile(src, test_dir + "/binance_ETH-USDT_5m.parquet")

    app = Dash("pdr_backend.statutil.arima_dash")
    app.config["suppress_callback_exceptions"] = True
    app.layout = get_layout()
    app.layout.children[0].data = test_dir
    get_callbacks(app)

    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("#error-message", "")
    dash_duo.find_element("#arima-graphs")

    _check_dashboard(dash_duo)
    dash_duo.find_element("#autocorelation-lag").send_keys("12")
    _check_dashboard(dash_duo)
    dash_duo.find_element("input[type='radio']").click()
    _check_dashboard(dash_duo, adf_text="BC=F,D=0")


def _check_dashboard(dash_duo, adf_text="BC=T,D=1"):
    dash_duo.wait_for_element("#seasonal_column #relativeEnergies")
    dash_duo.wait_for_element("#seasonal_column #seasonal_plots")
    dash_duo.wait_for_text_to_equal(
        "#seasonal_column #Seasonal-title",
        f"Seasonal Decomp. for {adf_text} ⓘ",
        timeout=20,
    )
    dash_duo.wait_for_element("#autocorelation_column #autocorelation")
    dash_duo.wait_for_element("#autocorelation_column #pautocorelation")
    dash_duo.wait_for_text_to_equal(
        "#autocorelation_column #Autocorelation-title", f"ACF & PACF for {adf_text} ⓘ"
    )
    dash_duo.wait_for_element("#transition_column #transition_table")
    dash_duo.wait_for_text_to_equal("#transition_column #Transition-title", "ADF ⓘ")


@enforce_types
def _get_data():
    """Return (start_ut, timeframe, yvals) for BTC 5min"""
    df = pd.read_csv(DATA_FILE)  # all data start_time = UnixTimeMs(df["timestamp"][0])
    st = UnixTimeMs(df["timestamp"][0])
    t = ArgTimeframe("5m")
    y = df[BTC_COL].array

    return (st, t, y)
