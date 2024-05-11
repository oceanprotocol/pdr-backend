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
        assert len(y_values.shape) == 1, "y_values must be 1d array"

        N_samples = len(y_values)
        adf_pvalue = adfuller(y_values)[1]
    
        target_CI = 0.95 # target 95% confidence interval
        alpha = 1.0 - target_CI
        acf_results = CorrResults(acf(y_values, nlags=nlags, alpha=alpha))
        pacf_results = CorrResults(pacf(y_values, nlags=nlags, alpha=alpha))
                
        plotdata = AutocorrelationPlotdata(
            N_samples, adf_pvalue, acf_results, pacf_results,
        )
    
        return plotdata

class CorrResults:
    @enforce_types
    def __init__(self, corr_results: tuple):
        """@arguments -- corr_results -- output of acf() or pacf()"""
        values = corr_results[0]
        ci_lower = np.array([pair[0] for pair in corr_results[1]])
        ci_upper = np.array([pair[1] for pair in corr_results[1]])
        ci_diff = ci_upper - ci_lower

        self.values = values
        self.lower_exclusion = - 1 * ci_diff
        self.upper_exclusion = + 1 * ci_diff
        
    @property
    def max_lag(self) -> int:
        return len(self.values)

    @property
    def x_lags(self) -> np.ndarray:
        return np.arange(0, self.max_lag)


@enforce_types
class AutocorrelationPlotdata:
    """Simple class to manage many inputs going to plot_autocorrelation."""

    def __init__(
            self,
            N_samples: int,
            adf_pvalue: float,
            acf_results: CorrResults,
            pacf_results: CorrResults,
    ):
        self.N_samples = N_samples
        self.adf_pvalue = adf_pvalue
        self.acf_results = acf_results
        self.pacf_results = pacf_results

    @property
    def max_lag(self) -> int:
        return self.acf_results.max_lag


@enforce_types
def plot_autocorrelation(autocorrelation_plotdata: AutocorrelationPlotdata):
    """
    @description
      Plot autocorrelation & partial autocorrelation
    """
    d = autocorrelation_plotdata

    fig = make_subplots(rows=2, cols=1, vertical_spacing=0.04)
    
    # subplot 1: acf
    _add_corr_traces(d.acf_results, fig, row=1)
    fig.update_yaxes(title_text="autocorrelation (acf)", row=1, col=1)

    # subplot 2: pacf
    _add_corr_traces(d.pacf_results, fig, row=2)
    fig.update_yaxes(title_text="partial autocorrelation (pacf)", row=2, col=1)
    fig.update_xaxes(title_text="lag", row=2, col=1)

    # global: set minor ticks
    minor = {"ticks": "inside", "showgrid": True}
    for row in [1, 2]:
        fig.update_yaxes(minor=minor, row=row, col=1)

    # global: share x-axes of subplots 1-2
    fig.update_layout(
        {
            "xaxis": {"matches": "x", "showticklabels": True},
            "xaxis2": {"matches": "x", "showticklabels": True},
        }
    )

    # global: other
    s = "Autocorr. & partial autocorr."
    s += f" for {d.N_samples} points"
    s += f". ADF p-value={compactSmallNum(d.adf_pvalue)}"
    fig.update_layout(title_text=s, showlegend=False)
    
    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=16)
    delta = 0.05 * d.max_lag
    fig.update_xaxes(range=[0 - delta, d.max_lag - delta])

    return fig

    
@enforce_types
def _add_corr_traces(corr_results: CorrResults, fig, row:int):
    """Worker function for plotting acf or pacf"""

    # exclusion region 
    # different than CIs! See https://stats.stackexchange.com/questions/518786/what-am-i-misunderstanding-about-the-acf-and-acf-plot
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.lower_exclusion,
            mode="lines",
            line={"color":"cornflowerblue", "width":0},
        ),
        row=row,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.upper_exclusion,
            fill="tonexty", # fill area between this trace and previous one
            mode="lines",
            line={"color":"cornflowerblue", "width":0},
        ),
        row=row,
        col=1,
    )

    # main values
    size = _rail(100 // corr_results.max_lag, 1, 10)
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.values,
            mode="markers",
            marker={"color":"blue", "size":size},
        ),
        row=row,
        col=1,
    )
    
    # vertical bars
    width = _rail(50 // corr_results.max_lag, 1, 10)
    for x, y in zip(corr_results.x_lags, corr_results.values):
        fig.add_trace(
            go.Scatter(
                x=[x, x],
                y=[0, y],
                mode="lines",
                line={"color": "black", "width": width},
            ),
            row=row,
            col=1,
        )

@enforce_types
def _rail(val:int, mn_val:int, mx_val:int) -> int:
    return max(mn_val, min(mx_val, val))
