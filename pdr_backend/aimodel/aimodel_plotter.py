#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from enforce_typing import enforce_types
from pdr_backend.sim.sim_plotter import empty_fig

from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata


@enforce_types
def plot_aimodel_response(aimodel_plotdata: AimodelPlotdata):
    """
    @description
      Plot the model response in a line plot (1 var) or contour plot (2 vars).
      And overlay X-data. (Training data or otherwise.)

    @arguments
      aimodel_plotdata --

    @return
      figure --
    """
    d = aimodel_plotdata

    if d.n_sweep == 1:
        return _plot_lineplot_1var(aimodel_plotdata)

    return _plot_contour(aimodel_plotdata)


@enforce_types
def _plot_lineplot_1var(aimodel_plotdata: AimodelPlotdata):
    """
    @description
      Do a 1d lineplot, when exactly 1 input x-var
      Will fail if not 1 var.
      Because one var total, we can show more info of true-vs-actual
    """
    # aimodel data
    d = aimodel_plotdata
    assert d.n_sweep == 1
    X, ytrue, ycont, y_thr = d.X_train, d.ytrue_train, d.ycont_train, d.y_thr

    # take 1 var
    nvars = X.shape[1]
    sweep_vars = aimodel_plotdata.sweep_vars
    assert nvars > 0
    if nvars == 1:
        chosen_i = 0
    elif sweep_vars is not None and len(sweep_vars) >= 1:
        chosen_i = sweep_vars[0]
    else:
        imps = d.model.importance_per_var()
        chosen_i = np.argsort(imps)[::-1][0]  # type:ignore[assignment]

    # base data
    x = X[:, chosen_i]
    colname = d.colnames[chosen_i]
    N = len(x)

    # calc mesh_X = uniform grid on chosen_i,
    #  and every other dimension i has value slicing_x[i]
    mesh_chosen_x = np.linspace(min(x), max(x), 200)
    slicing_X = np.reshape(d.slicing_x, (1, nvars))  # [0][var_i]
    mesh_N = len(mesh_chosen_x)
    mesh_X = np.repeat(slicing_X, mesh_N, axis=0)  # [sample_i][var_i]
    mesh_X[:, chosen_i] = mesh_chosen_x

    # calc model classifier response
    mesh_yptrue_hat = d.model.predict_ptrue(mesh_X)
    ytrue_hat = d.model.predict_true(X)

    # calc model regressor response
    mesh_ycont_hat = None
    if d.model.do_regr:
        mesh_ycont_hat = d.model.predict_ycont(mesh_X)

    # build up "fig"...
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # orange vertical bars: where classifier was wrong
    correct = ytrue_hat == ytrue
    wrong = np.invert(correct)
    for i, xi in enumerate(x[wrong]):
        label = "classif: wrong" if i == 0 else None
        fig.add_trace(
            go.Scatter(
                x=[xi, xi],
                y=[0.0, 1.0],
                mode="lines",
                line={"color": "orange", "width": 1},
                name=label,
                showlegend=bool(label),
            )
        )

    # blue line curve: classifier probability response
    fig.add_trace(
        go.Scatter(
            x=mesh_chosen_x,
            y=mesh_yptrue_hat,
            mode="lines",
            line={"color": "blue"},
            name="classif: model prob(true)",
        )
    )

    # scatterplots blue=training_T, brown=training_F
    jj = _get_jitter(N)
    yfalse = np.invert(ytrue)
    y1 = ytrue[ytrue] - jj[ytrue] + 0.015
    y2 = ytrue[yfalse] + jj[yfalse] - 0.015

    fig.add_trace(
        go.Scatter(
            x=x[ytrue],
            y=y1,
            mode="markers",
            marker={"color": "blue", "size": 5},
            name="classif: trn data class=true",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x[yfalse],
            y=y2,
            mode="markers",
            marker={"color": "brown", "size": 5},
            name="classif: trn data class=false",
        )
    )
    fig.update_yaxes(title_text="classif: prob(True)", secondary_y=False)

    # line plot: regressor response, training data
    if d.model.do_regr:
        assert mesh_ycont_hat is not None
        assert y_thr is not None
        assert ycont is not None
        fig.add_trace(
            go.Scatter(
                x=mesh_chosen_x,
                y=mesh_ycont_hat,
                mode="lines",
                line={"color": "black"},
                name="regr: model yhat",
            ),
            secondary_y=True,
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=ycont,
                mode="markers",
                marker={"color": "black", "size": 5},
                name="regr: trn data y",
            ),
            secondary_y=True,
        )
        fig.add_trace(
            go.Scatter(
                x=[min(mesh_chosen_x), max(mesh_chosen_x)],
                y=[y_thr, y_thr],
                mode="lines",
                line={"color": "black", "dash": "dot"},
                name="regr: threshold up/down",
            ),
            secondary_y=True,
        )
        fig.update_yaxes(title_text="regr: y-value", secondary_y=True)

    fig.update_xaxes(title_text=colname)

    return fig


@enforce_types
def _plot_contour(aimodel_plotdata: AimodelPlotdata):
    """
    @description
      Plot the model, when there's >=2 input x-vars. Use a contour plot.
      If >2 vars, it plots the 2 most important vars. Will fail if <2 vars.
      It overlays X-data. (Training data or otherwise.)

    @arguments
      aimodel_plotdata --
    """
    # pylint: disable=too-many-statements
    # aimodel data
    d = aimodel_plotdata
    X = d.X_train
    nvars = d.n
    assert nvars >= 2

    # take 2 vars
    nvars = X.shape[1]
    sweep_vars = aimodel_plotdata.sweep_vars
    assert nvars > 1
    if nvars == 1:
        chosen_I = [0, 0]
    elif nvars == 2:
        chosen_I = [0, 1]
    elif sweep_vars is not None and len(sweep_vars) >= 2:
        chosen_I = list(sweep_vars)[:2]
    else:
        imps = d.model.importance_per_var()
        chosen_I = np.argsort(imps)[::-1][:2]  # type:ignore[assignment]
    chosen_X = X[:, chosen_I]
    chosen_colnames = [d.colnames[i] for i in chosen_I]

    # calc min/max
    x0_min, x0_max = min(chosen_X[:, 0]), max(chosen_X[:, 0])
    x1_min, x1_max = min(chosen_X[:, 1]), max(chosen_X[:, 1])

    # calc mesh_X = uniform grid across two most important dimensions,
    #  and every other dimension i has value slicing_x[i]
    feature_x = np.linspace(x0_min, x0_max, 200)
    feature_y = np.linspace(x1_min, x1_max, 200)
    dim0, dim1 = np.meshgrid(feature_x, feature_y)
    mesh_0, mesh_1 = dim0.ravel(), dim1.ravel()
    mesh_chosen_X = np.array([mesh_0, mesh_1]).T  # [sample_i][chosen_var_i]
    slicing_X = np.reshape(d.slicing_x, (1, nvars))  # [0][var_i]
    mesh_N = mesh_chosen_X.shape[0]
    mesh_X = np.repeat(slicing_X, mesh_N, axis=0)  # [sample_i][var_i]
    mesh_X[:, chosen_I] = mesh_chosen_X

    # make subplots
    s1 = "classif: contours = model prob(true)"
    s2 = "regr: contours = model y-value"
    if d.model.do_regr:
        fig = make_subplots(
            rows=2, cols=1, subplot_titles=[s1, s2], vertical_spacing=0.07
        )
    else:
        fig = make_subplots(rows=1, cols=1, subplot_titles=s1)

    # subplot at row 1: classifier response
    Z = d.model.predict_ptrue(mesh_X)
    colorscale = "RdBu"  # red=False, blue=True, white=between
    _add_contour_subplot(d, chosen_I, dim0, dim1, Z, colorscale, fig, row=1)

    # subplot at row 2: regressor response
    if d.model.do_regr:
        Z = d.model.predict_ycont(mesh_X)
        colorscale = "Greys"
        _add_contour_subplot(d, chosen_I, dim0, dim1, Z, colorscale, fig, row=2)

    # global: axes ranges
    fig.update_xaxes(range=[x0_min, x0_max])
    fig.update_yaxes(range=[x1_min, x1_max])

    # global: axes labels
    xlabel_row = 2 if d.model.do_regr else 1
    fig.update_xaxes(title=chosen_colnames[0], row=xlabel_row, col=1)
    fig.update_yaxes(title=chosen_colnames[1])

    return fig


@enforce_types
# pylint: disable=too-many-positional-arguments
def _add_contour_subplot(d, chosen_I, dim0, dim1, Z, colorscale, fig, row):
    """In-place update 'fig' at specified subplot row"""
    Z = Z.reshape(dim1.shape)

    # base data
    X = d.X_train
    ytrue = d.ytrue_train
    chosen_X = X[:, chosen_I]

    # calc other data for plots
    ytrue_hat = d.model.predict_true(X)
    correct = ytrue_hat == ytrue
    wrong = np.invert(correct)
    yfalse = np.invert(ytrue)

    # contour plot: model response
    fig.add_trace(
        go.Contour(
            z=Z,
            x=dim0[0],
            y=dim1[:, 0],
            showscale=False,
            line_width=0,
            ncontours=25,
            colorscale=colorscale,
        ),
        row=row,
        col=1,
    )

    # scatterplots: orang_outline=misclassified
    fig.add_trace(
        go.Scatter(
            x=chosen_X[:, 0][wrong],
            y=chosen_X[:, 1][wrong],
            mode="markers",
            marker={"color": "orange", "size": 10},
            name="classif: wrong",
            showlegend=(row == 1),
        ),
        row=row,
        col=1,
    )

    # scatterplots: blue=training_T
    fig.add_trace(
        go.Scatter(
            x=chosen_X[:, 0][ytrue],
            y=chosen_X[:, 1][ytrue],
            mode="markers",
            marker={"color": "blue", "size": 5},
            name="true",
            showlegend=(row == 1),
        ),
        row=row,
        col=1,
    )

    # scatterplots: brown=training_F
    fig.add_trace(
        go.Scatter(
            x=chosen_X[:, 0][yfalse],
            y=chosen_X[:, 1][yfalse],
            mode="markers",
            marker={"color": "brown", "size": 5},
            name="false",
            showlegend=(row == 1),
        ),
        row=row,
        col=1,
    )


@enforce_types
def plot_aimodel_varimps(d: AimodelPlotdata):
    """
    @description
      Bar plot showing rel importance of vars
      Including 95% confidence intervals (2.0 stddevs)

    @arguments
      d -- AimodelPlotdata
    """
    try:
        imps_avg, imps_stddev = d.model.importance_per_var(include_stddev=True)
    except Exception:
        return empty_fig("Can't plot var imp for chain data")

    imps_avg = imps_avg + 1e-15  # give imp > 0, so before dummy vars in plot
    varnames = d.colnames
    n = len(varnames)

    sweep_vars = d.sweep_vars if hasattr(d, "sweep_vars") else []

    # if >40 vars, truncate to top 40+1
    if n > 40:
        rest_avg = sum(imps_avg[40:])
        rest_stddev = np.average(imps_stddev[40:])
        imps_avg = np.append(imps_avg[:40], rest_avg)
        imps_stddev = np.append(imps_stddev[:40], rest_stddev)
        varnames = varnames[:40] + ["rest"]
        n = 40 + 1

    # if <10 vars, make it like 10
    if n < 10:
        n_extra = 10 - n
        imps_avg = np.append(imps_avg, [0.0] * n_extra)
        imps_stddev = np.append(imps_stddev, [0.0] * n_extra)
        varnames = varnames + [""] * n_extra
        n = 10

    # put in percent scales
    imps_avg = imps_avg * 100.0
    imps_stddev = imps_stddev * 100.0
    imps_lower = np.clip(imps_avg - imps_stddev * 2.0, 0.0, np.inf)
    imps_upper = imps_avg + imps_stddev * 2.0
    error_x_lower = imps_avg - imps_lower
    error_x_upper = imps_upper - imps_avg

    labelalias = {}
    colors = []

    for i in range(n):
        # avoid overlap in figure by giving different labels,
        # but alias them to "" for the legend
        if varnames[i] == "":
            varnames[i] = f"var{i}"
            labelalias[varnames[i]] = ""

        colors.append("#636EFA" if not sweep_vars or i in sweep_vars else "#D4D5DD")

    # build up "fig"...
    fig = go.Figure()

    # bar plot
    fig.add_trace(
        go.Bar(
            x=imps_avg,
            y=varnames,
            error_x={
                "type": "data",
                "array": error_x_upper,
                "arrayminus": error_x_lower,
            },
            orientation="h",
            marker_color=colors,
        )
    )

    bar_lw = 0.2 if n < 15 else 0.3
    err_lw = 3 if n < 15 else 1
    fig.update_traces(
        marker_line_width=bar_lw,
        error_x_width=err_lw,
    )

    fig.update_layout(
        yaxis={
            "categoryorder": "total ascending",
            "labelalias": labelalias,
        }
    )
    fig.update_layout(xaxis_title="Relative importance (%)")
    fig.update_layout(title="Variable importances")

    return fig


J = np.array([], dtype=float)  # jitter


@enforce_types
def _get_jitter(N: int) -> np.ndarray:
    global J
    while J.shape[0] < N:
        J = np.append(J, np.random.rand())
    return J[:N]
