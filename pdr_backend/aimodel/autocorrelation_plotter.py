import numpy as np
import plotly.graph_objects as go
from enforce_typing import enforce_types

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