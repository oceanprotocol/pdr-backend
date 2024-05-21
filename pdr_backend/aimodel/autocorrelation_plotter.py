import numpy as np
import plotly.graph_objects as go
from enforce_typing import enforce_types
import plotly.express as px

from pdr_backend.aimodel.autocorrelation import AutocorrelationPlotdata


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
def plot_autocorrelation_plotly(autocorrelation_plotdata: AutocorrelationPlotdata):
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