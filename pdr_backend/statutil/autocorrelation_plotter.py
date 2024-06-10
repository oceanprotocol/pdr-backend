import numpy as np
import plotly.graph_objects as go
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
    title = "Autocorrelation (ACF)"
    fig = go.Figure()
    _add_corr_traces(corr_results, title, fig)
    return fig


@enforce_types
def plot_pacf(autocorrelation_plotdata: AutocorrelationPlotdata):
    corr_results = autocorrelation_plotdata.pacf_results
    title = "Partial Autocorrelation (PACF)"
    fig = go.Figure()
    _add_corr_traces(corr_results, title, fig)
    return fig


@enforce_types
def _add_corr_traces(corr_results: CorrResults, title_s: str, fig):
    """Worker function for plotting acf or pacf"""

    # exclusion region
    # different than CIs! See https://stats.stackexchange.com/questions/518786/what-am-i-misunderstanding-about-the-acf-and-acf-plot # pylint: disable=line-too-long
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.lower_exclusion,
            mode="lines",
            line={"color": "cornflowerblue", "width": 0},
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.upper_exclusion,
            fill="tonexty",  # fill area between this trace and previous one
            mode="lines",
            line={"color": "cornflowerblue", "width": 0},
        ),
    )

    # main values
    size = _rail(100 // corr_results.max_lag, 1, 10)
    fig.add_trace(
        go.Scatter(
            x=corr_results.x_lags,
            y=corr_results.values,
            mode="markers",
            marker={"color": "blue", "size": size},
        ),
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
        )

    # x-axis label
    fig.update_xaxes(title="lag")

    # y-axis
    fig.update_yaxes(title=title_s, minor={"ticks": "inside", "showgrid": True})

    # ticks
    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=16)

    # x-axis range
    max_lag = corr_results.max_lag
    delta = 0.05 * max_lag
    fig.update_xaxes(range=[0 - delta, max_lag - delta])

    # layout
    fig.update_layout(
        title={
            "text": title_s,
            "y": 0.96,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        margin={"l": 5, "r": 5, "t": 50, "b": 0},
        showlegend=False,
    )


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
    fig.update_yaxes(title_text="Transition")
    fig.update_xaxes(title_text="ADF")
    fig.update_layout(
        margin={"l": 5, "r": 5, "t": 20, "b": 0},
        xaxis={"range": [0.05, 0.1]},
    )
    return fig
