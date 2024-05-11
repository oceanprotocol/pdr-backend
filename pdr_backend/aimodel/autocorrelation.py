from datetime import datetime
from typing import List

from enforce_typing import enforce_types
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.stattools import acf, pacf

from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.util.mathutil import has_nan
from pdr_backend.util.time_types import UnixTimeMs


class AutocorrelationPlotdataFactory:

    @classmethod
    def build(cls, y_values) -> "AutocorrelationPlotdata":
        # preconditions
        assert len(y_values.shape) == 1, "y_values must be 1d array"

        acf_values = acf(y_values)
        pacf_values = pacf(y_values)
        
        return AutocorrelationPlotdata(acf_values, pacf_values)


class AutocorrelationPlotdata:
    """Simple class to manage many inputs going to plot_autocorrelation."""

    @enforce_types
    def __init__(
        self,
        acf_values: np.ndarray,
        pacf_values: np.ndarray,
    ):
        self.acf_values = acf_values
        self.pacf_values = pacf_values

    @property
    def max_lag(self) -> int:
        return len(self.acf_values)

    @property
    def x_lags(self) -> np.ndarray:
        return np.arange(1, self.max_lag+1)

    
@enforce_types
def plot_autocorrelation(autocorrelation_plotdata: AutocorrelationPlotdata):
    """
    @description
      Plot autocorrelation & partial autocorrelation
    """
    d = autocorrelation_plotdata
    x = d.x_lags

    fig = make_subplots(rows=2, cols=1, vertical_spacing=0.02)

    # subplot 1: observed
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.acf_values,
            mode="lines",
            line={"color": "red", "width": 1},
        ),
        row=1,
        col=1,
    )
    fig.update_yaxes(title_text="autocorrelation (acf)", row=1, col=1)

    # subplot 2: observed
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.acf_values,
            mode="lines",
            line={"color": "red", "width": 1},
        ),
        row=2,
        col=1,
    )
    fig.update_yaxes(title_text="partial autocorrelation (pacf)", row=2, col=1)
    fig.update_xaxes(title_text="lag", row=5, col=1)

    # global: set minor ticks
    minor = {"ticks": "inside", "showgrid": True}
    fig.update_yaxes(minor=minor, row=1, col=1)
    for row in [2, 3, 4, 5]:
        fig.update_yaxes(minor=minor, row=row, col=1)
        fig.update_xaxes(minor=minor, row=row, col=1)

    # global: share x-axes of subplots 2-5
    fig.update_layout(
        {
            "xaxis": {"matches": "x", "showticklabels": False},
            "xaxis2": {"matches": "x", "showticklabels": True},
        }
    )

    # global: other
    fig.update_layout(
        title_text="Autocorrelation & partial autocorrelation",
        showlegend=False,
    )
    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=15)

    return fig
