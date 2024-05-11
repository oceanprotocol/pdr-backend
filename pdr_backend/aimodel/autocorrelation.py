from datetime import datetime
from typing import List

from enforce_typing import enforce_types
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.stattools import acf, adfuller, pacf

from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.util.mathutil import has_nan
from pdr_backend.util.strutil import compactSmallNum
from pdr_backend.util.time_types import UnixTimeMs


class AutocorrelationPlotdataFactory:

    @classmethod
    def build(cls, y_values, nlags:int) -> "AutocorrelationPlotdata":
        # preconditions
        assert len(y_values.shape) == 1, "y_values must be 1d array"

        adf_pvalue = adfuller(y_values)[1]
    
        target_CI = 0.95 # target 95% confidence interval
        alpha = 1.0 - target_CI
        acf_results = acf(y_values, nlags=nlags, alpha=alpha)
        pacf_results = pacf(y_values, nlags=nlags, alpha=alpha)
                
        plotdata = AutocorrelationPlotdata(
            adf_pvalue, acf_results, pacf_results,
        )
    
        return plotdata


class AutocorrelationPlotdata:
    """Simple class to manage many inputs going to plot_autocorrelation."""

    @enforce_types
    def __init__(self, adf_pvalue: float, acf_results, pacf_results):
        self.adf_pvalue = adf_pvalue
        
        self.acf_values = acf_results[0]
        self.acf_lower = [pair[0] for pair in acf_results[1]]
        self.acf_upper = [pair[1] for pair in acf_results[1]]
        
        self.pacf_values = pacf_results[0]
        self.pacf_lower = [pair[0] for pair in pacf_results[1]]
        self.pacf_upper = [pair[0] for pair in pacf_results[1]]
        
    @property
    def max_lag(self) -> int:
        return len(self.acf_values)

    @property
    def x_lags(self) -> np.ndarray:
        return np.arange(self.max_lag)

    
def _add_corr_traces(x_lags:np.ndarray, corr_values:np.ndarray, fig, row:int):
    for x, y in zip(x_lags, corr_values):
        fig.add_trace(
            go.Scatter(
                x=[x, x],
                y=[0, y],
                mode="lines",
                line={"color": "black", "width": 5},
            ),
            row=row,
            col=1,
        )
        
    fig.add_trace(
        go.Scatter(
            x=x_lags,
            y=corr_values,
            mode="markers",
            marker={"color":"blue", "size":8},
        ),
        row=row,
        col=1,
    )
    
@enforce_types
def plot_autocorrelation(autocorrelation_plotdata: AutocorrelationPlotdata):
    """
    @description
      Plot autocorrelation & partial autocorrelation
    """
    d = autocorrelation_plotdata

    fig = make_subplots(rows=2, cols=1, vertical_spacing=0.02)
    
    # subplot 1: acf
    _add_corr_traces(d.x_lags, d.acf_values, fig, row=1)
    fig.update_yaxes(title_text="autocorrelation (acf)", row=1, col=1)

    # subplot 2: pacf
    _add_corr_traces(d.x_lags, d.pacf_values, fig, row=2)
    fig.update_yaxes(title_text="partial autocorrelation (pacf)", row=2, col=1)

    # global: x-axis
    fig.update_xaxes(title_text="lag", row=2, col=1)

    # global: set minor ticks
    minor = {"ticks": "inside", "showgrid": True}
    for row in [1, 2]:
        fig.update_yaxes(minor=minor, row=row, col=1)

    # global: share x-axes of subplots 1-2
    fig.update_layout(
        {
            "xaxis": {"matches": "x", "showticklabels": False},
            "xaxis2": {"matches": "x", "showticklabels": True},
        }
    )

    # global: other
    s_pvalue = f"ADF p-value={compactSmallNum(d.adf_pvalue)}"
    fig.update_layout(
        title_text=f"Autocorr. & partial autocorr. {s_pvalue}",
        showlegend=False,
    )
    fig.update_yaxes(nticks=8)
    x_buffer = 0.05 * d.max_lag 
    fig.update_xaxes(range=[0 - x_buffer, d.max_lag + x_buffer])

    return fig
