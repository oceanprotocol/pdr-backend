import numpy as np
import plotly.graph_objects as go
from enforce_typing import enforce_types
from plotly.subplots import make_subplots
from statsmodels.tsa.stattools import adfuller

from pdr_backend.statutil.autocorrelation import (
    AutocorrelationPlotdata,
    _add_corr_traces,
)
from pdr_backend.statutil.boxcox import safe_boxcox


@enforce_types
def plot_acf(autocorrelation_plotdata: AutocorrelationPlotdata):
    """
    @description
      Plot autocorrelation function (ACF)
    """
    d = autocorrelation_plotdata
    fig = make_subplots(rows=1, cols=1)

    _add_corr_traces(d.acf_results, fig, row=1)
    fig.update_xaxes(title_text="lag", row=1, col=1)

    # Set minor ticks
    minor = {"ticks": "inside", "showgrid": True}
    fig.update_yaxes(minor=minor, row=1, col=1)

    # Layout settings
    fig.update_layout(
        margin={"l": 5, "r": 5, "t": 20, "b": 0},
        showlegend=False,
    )

    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=16)
    delta = 0.05 * d.max_lag
    fig.update_xaxes(range=[0 - delta, d.max_lag - delta])

    return fig


@enforce_types
def plot_pacf(autocorrelation_plotdata: AutocorrelationPlotdata):
    """
    @description
      Plot partial autocorrelation function (PACF)
    """
    d = autocorrelation_plotdata
    fig = make_subplots(rows=1, cols=1)

    _add_corr_traces(d.pacf_results, fig, row=1)
    fig.update_xaxes(title_text="lag", row=1, col=1)

    # Set minor ticks
    minor = {"ticks": "inside", "showgrid": True}
    fig.update_yaxes(minor=minor, row=1, col=1)

    # Layout settings
    fig.update_layout(
        title={
            "text": "Partial Autocorrelation (PACF)",
            "y": 0.96,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        margin={"l": 5, "r": 5, "t": 50, "b": 0},
        showlegend=False,
    )

    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=16)
    delta = 0.05 * d.max_lag
    fig.update_xaxes(range=[0 - delta, d.max_lag - delta])

    return fig


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
