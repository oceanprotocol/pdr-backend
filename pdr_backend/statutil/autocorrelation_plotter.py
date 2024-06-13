import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from enforce_typing import enforce_types
from statsmodels.tsa.stattools import adfuller

from pdr_backend.statutil.autocorrelation_plotdata import (
    AutocorrelationPlotdata,
    CorrResults,
)
from pdr_backend.statutil.boxcox import safe_boxcox


@enforce_types
def plot_acf(autocorrelation_plotdata: AutocorrelationPlotdata):
    corr_results = autocorrelation_plotdata.acf_results
    ylabel = "Autocorrelation (ACF)"
    fig = make_subplots(rows=1, cols=1, subplot_titles=(ylabel,))
    add_corr_traces(fig, corr_results, row=1, col=1, ylabel=ylabel)
    return fig


@enforce_types
def plot_pacf(autocorrelation_plotdata: AutocorrelationPlotdata):
    corr_results = autocorrelation_plotdata.pacf_results
    ylabel = "Partial Autocorrelation (PACF)"
    fig = make_subplots(rows=1, cols=1, subplot_titles=(ylabel,))
    add_corr_traces(fig, corr_results, row=1, col=1, ylabel=ylabel)
    return fig


@enforce_types
def add_corr_traces(fig, corr_results: CorrResults, row:int, col:int, ylabel):
    """Worker function for plotting acf or pacf"""

    # exclusion region
    # different than CIs! See https://stats.stackexchange.com/questions/518786/what-am-i-misunderstanding-about-the-acf-and-acf-plot # pylint: disable=line-too-long
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.lower_exclusion,
            mode="lines",
            line={"color": "cornflowerblue", "width": 0},
            showlegend=False,
        ),
        row=row,
        col=col,
    )
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.upper_exclusion,
            fill="tonexty",  # fill area between this trace and previous one
            mode="lines",
            line={"color": "cornflowerblue", "width": 0},
            showlegend=False,
        ),
        row=row,
        col=col,
    )

    # main values
    size = _rail(100 // corr_results.max_lag, 1, 10)
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.values,
            mode="markers",
            marker={"color": "blue", "size": size},
            showlegend=False,
        ),
        row=row,
        col=col,
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
                showlegend=False,
            ),
            row=row,
            col=col,
        )

    # x-axis label
    fig.update_xaxes(title="lag", row=row, col=col)

    # y-axis
    minor_d = {"ticks": "inside", "showgrid": True}
    fig.update_yaxes(title=ylabel, minor=minor_d, row=row, col=col)

    # ticks
    fig.update_yaxes(nticks=8, row=row, col=col)
    fig.update_xaxes(nticks=16, row=row, col=col)

    # x-axis range
    max_lag = corr_results.max_lag
    delta = 0.05 * max_lag
    fig.update_xaxes(range=[0 - delta, max_lag - delta], row=row, col=col)

@enforce_types
def _rail(val: int, mn_val: int, mx_val: int) -> int:
    return max(mn_val, min(mx_val, val))


@enforce_types
def get_transitions(selected_idx=None, y=[]):
    bar_colors = ["white"] * 4  # Default bar color
    if selected_idx is not None:
        bar_colors[selected_idx] = "grey"  # Change color of the selected bar

    labels = ["BC=T,D=2", "BC=T,D=1", "BC=T,D=0", "BC=F,D=0"]

    adf_results = {}

    # No transformation
    adf_result = adfuller(y)
    adf_results["BC=F,D=0"] = adf_result

    # Box-Cox transformation without differencing
    y_bc = safe_boxcox(y)
    adf_result = adfuller(y_bc)
    adf_results["BC=T,D=0"] = adf_result

    # Box-Cox transformation with differencing
    y_bc_diff = np.diff(y_bc)
    adf_result = adfuller(y_bc_diff)
    adf_results["BC=T,D=1"] = adf_result

    # Box-Cox transformation with second differencing
    y_bc_diff2 = np.diff(y_bc_diff)
    adf_result = adfuller(y_bc_diff2)
    adf_results["BC=T,D=2"] = adf_result

    adf_values = [adf_results[label][1] for label in labels]

    fig = go.Figure(
        data=[
            go.Bar(
                x=[1, 1, 1, 1],
                y=labels,
                orientation="h",
                width=0.3,
                marker_color=bar_colors,
                showlegend=False,
            ),
            go.Bar(
                x=adf_values,
                y=labels,
                orientation="h",
                marker_color=["blue"] * 4,
                width=0.3,
                showlegend=False,
            ),
        ]
    )
    fig.update_yaxes(title_text="Transformation")
    fig.update_xaxes(title_text="ADF")
    fig.update_layout(
        margin={"l": 5, "r": 5, "t": 20, "b": 0},
        xaxis={"range": [0.05, 0.1]},
    )
    return fig
