import numpy as np
import plotly.graph_objects as go
from enforce_typing import enforce_types
from plotly.subplots import make_subplots

from pdr_backend.aimodel.autocorrelation import (
    AutocorrelationPlotdata,
    _add_corr_traces,
)


@enforce_types
def plot_autocorrelation(data: AutocorrelationPlotdata):
    """
    @description
      Do a 1d lineplot, when >1 input x-var, and we have chosen the var.
      Because >1 var total, we can show more info of true-vs-actual
    """
    # input data
    d = data
    assert d.acf_results >= 1

    # construct sweep_x
    sweepvar_i = d.sweep_vars[0]  #  type: ignore[index]
    mn_x, mx_x = min(d.X_train[:, sweepvar_i]), max(d.X_train[:, sweepvar_i])
    N = 200
    sweep_x = np.linspace(mn_x, mx_x, N)

    # construct X
    X = np.empty((N, d.n), dtype=float)
    X[:, sweepvar_i] = sweep_x
    for var_i in range(d.n):
        if var_i == sweepvar_i:
            continue
        X[:, var_i] = d.slicing_x[var_i]

    # calc model response
    yptrue = d.model.predict_ptrue(X)  # [sample_i]: prob_of_being_true

    # line plot: model response surface
    fig_line = go.Figure(
        data=go.Scatter(
            x=sweep_x,
            y=yptrue,
            mode="lines",
            line={"color": "#636EFA"},
            name="model prob(true)",
        )
    )

    return fig_line


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
        title={
            "text": "Autocorrelation (ACF)",
            "y": 0.96,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        margin=dict(l=5, r=5, t=50, b=0),
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
        margin=dict(l=5, r=5, t=50, b=0),
        showlegend=False,
    )

    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=16)
    delta = 0.05 * d.max_lag
    fig.update_xaxes(range=[0 - delta, d.max_lag - delta])

    return fig
