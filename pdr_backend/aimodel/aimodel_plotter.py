from enforce_typing import enforce_types
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import altair as alt

from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata


@enforce_types
def plot_aimodel_response(
    aimodel_plotdata: AimodelPlotdata,
):
    """
    @description
      Plot the model response in a line plot (1 var) contour plot (>1 vars)
      And overlay X-data. (Training data or otherwise.)
      If the model has >2 vars, it plots the 2 most important vars.

    @arguments
      aimodel_plotdata -- holds:
        model -- Aimodel
        X_train -- array [sample_i][var_i]:floatval -- trn model inputs (or other)
        ytrue_train -- array [sample_i]:boolval -- trn model outputs (or other)
        colnames -- list [var_i]:X_column_name
        slicing_x -- arrat [var_i]:floatval - when >2 dims, plot about this pt
      fig_ax -- None or (fig, ax) to easily embed into existing plot
      legend_loc -- eg "upper left". Applies only to contour plots.
    """
    if aimodel_plotdata.n == 1:
        return _plot_aimodel_lineplot(aimodel_plotdata)

    return _plot_aimodel_contour(aimodel_plotdata)


J = np.array([], dtype=float)  # jitter


@enforce_types
def _plot_aimodel_lineplot(aimodel_plotdata: AimodelPlotdata):
    """
    @description
      Plot the model, when there's 1 input x-var. Use a line plot.
      Will fail if not 1 var.
    """
    # aimodel data
    assert aimodel_plotdata.n == 1
    d = aimodel_plotdata
    X, ytrue = d.X_train, d.ytrue_train

    x = X[:, 0]
    N = len(x)

    # calc mesh_X = uniform grid
    mesh_x = np.linspace(min(x), max(x), 200)
    mesh_N = len(mesh_x)
    mesh_X = np.reshape(mesh_x, (mesh_N, 1))

    # calc z = model operating on mesh_X
    z = d.model.predict_ptrue(mesh_X)

    # calc ytrue_hat - model's response
    ytrue_hat = d.model.predict_true(X)

    # yellow vertical bars = where model was wrong
    correct = ytrue_hat == ytrue
    wrong = np.invert(correct)

    fig_bars = go.Figure()

    for i, xi in enumerate(x[wrong]):
        label = "wrong" if i == 0 else None
        fig_bars.add_trace(
            go.Scatter(
                x=[xi, xi],
                y=[0.0, 1.0],
                mode="lines",
                line={"color": "yellow", "width": 1},
                name=label,
                showlegend=bool(label),
            )
        )

    # line plot: model response surface
    fig_line = go.Figure(
        data=go.Scatter(
            x=mesh_x,
            y=z,
            mode="lines",
            line={"color": "gray"},
            name="model prob(true)",
        )
    )

    # scatterplots: cyan=training_T, red=training_F
    global J
    while J.shape[0] < N:
        J = np.append(J, np.random.rand() * 0.05)
    yfalse = np.invert(ytrue)
    y1 = ytrue[ytrue] - J[ytrue] + 0.025
    y2 = ytrue[yfalse] + J[yfalse] - 0.025

    fig_scatter_true = go.Figure(
        data=go.Scatter(
            x=x[ytrue],
            y=y1,
            mode="markers",
            marker={"color": "cyan", "size": 5},
            name="trn data true",
        )
    )

    fig_scatter_false = go.Figure(
        data=go.Scatter(
            x=x[yfalse],
            y=y2,
            mode="markers",
            marker={"color": "red", "size": 5},
            name="trn data false",
        )
    )

    fig_scatter_true.add_trace(fig_scatter_false.data[0])
    fig_scatter_true.add_trace(fig_line.data[0])

    fig_bars.add_trace(fig_scatter_true.data[0])
    fig_bars.add_trace(fig_scatter_true.data[1])
    fig_bars.add_trace(fig_scatter_true.data[2])

    return fig_bars


@enforce_types
def _plot_aimodel_contour(
    aimodel_plotdata: AimodelPlotdata,
):
    """
    @description
      Plot the model, when there's >=2 input x-vars. Use a contour plot.
      If >2 vars, it plots the 2 most important vars. Will fail if <2 vars.
      It overlays X-data. (Training data or otherwise.)
    """
    # aimodel data
    d = aimodel_plotdata
    X, ytrue = d.X_train, d.ytrue_train
    nvars = d.n
    assert nvars >= 2

    # take 2 most impt vars
    nvars = X.shape[1]
    assert nvars > 1
    if nvars == 1:
        impt_I = [0, 0]
    elif nvars == 2:
        impt_I = [0, 1]
    else:
        imps = d.model.importance_per_var()
        impt_I = np.argsort(imps)[::-1][:2]  # type:ignore[assignment]
    impt_X = X[:, impt_I]
    impt_colnames = [d.colnames[i] for i in impt_I]

    # calc min/max
    x0_min, x0_max = min(impt_X[:, 0]), max(impt_X[:, 0])
    x1_min, x1_max = min(impt_X[:, 1]), max(impt_X[:, 1])

    # calc mesh_X = uniform grid across two most important dimensions,
    #  and every other dimension i has value slicing_x[i]
    feature_x = np.linspace(x0_min, x0_max, 200)
    feature_y = np.linspace(x1_min, x1_max, 200)
    dim0, dim1 = np.meshgrid(feature_x, feature_y)
    mesh_0, mesh_1 = dim0.ravel(), dim1.ravel()
    mesh_impt_X = np.array([mesh_0, mesh_1]).T  # [sample_i][impt_var_i]
    slicing_X = np.reshape(d.slicing_x, (1, nvars))  # [0][var_i]
    mesh_N = mesh_impt_X.shape[0]
    mesh_X = np.repeat(slicing_X, mesh_N, axis=0)  # [sample_i][var_i]
    mesh_X[:, impt_I] = mesh_impt_X

    # calc Z = model operating on mesh_X
    Z = d.model.predict_ptrue(mesh_X).reshape(dim1.shape)

    # scatterplots: cyan=training_T, red=training_F, yellow_outline=misclassify
    ytrue_hat = d.model.predict_true(X)
    correct = ytrue_hat == ytrue
    wrong = np.invert(correct)

    yfalse = np.invert(ytrue)

    fig = go.Figure(
        data=go.Contour(
            z=Z,
            x=dim0[0],
            y=dim1[:, 0],
            showscale=False,
            line_width=0,
            ncontours=25,
            colorscale="RdBu",
        )
    )

    fig_scatter = go.Figure(
        data=go.Scatter(
            x=impt_X[:, 0][wrong],
            y=impt_X[:, 1][wrong],
            mode="markers",
            marker={"color": "yellow", "size": 10},
            name="wrong",
        )
    )

    fig_true = go.Figure(
        data=go.Scatter(
            x=impt_X[:, 0][ytrue],
            y=impt_X[:, 1][ytrue],
            mode="markers",
            marker={"color": "cyan", "size": 5},
            name="true",
        )
    )
    fig_false = go.Figure(
        data=go.Scatter(
            x=impt_X[:, 0][yfalse],
            y=impt_X[:, 1][yfalse],
            mode="markers",
            marker={"color": "red", "size": 5},
            name="false",
        )
    )

    fig.add_trace(fig_scatter.data[0])
    fig.add_trace(fig_true.data[0])
    fig.add_trace(fig_false.data[0])

    fig.update_layout(yaxis={"range": [x1_min, x1_max]})
    fig.update_layout(xaxis={"range": [x0_min, x0_max]})
    fig.update_xaxes(title_text=impt_colnames[0])
    fig.update_yaxes(title_text=impt_colnames[1])
    fig.update_layout(title="Contours = model response")

    return fig


@enforce_types
def plot_aimodel_varimps(d: AimodelPlotdata):
    """
    @description
      Bar plot showing rel importance of vars
      Including 95% confidence intervals (2.0 stddevs)

    @arguments
      d -- AimodelPlotdata
    """
    var_imps, errors = d.model.importance_per_var(include_stddev=True)
    labels = d.colnames

    var_imps = [100 * a for a in var_imps]
    errors = [100 * a for a in errors]

    df = pd.DataFrame(var_imps, columns=["importance"])
    df["label"] = labels
    df["erorrs"] = errors
    df["low"] = df["importance"] - df["erorrs"] * 2
    df["high"] = df["importance"] + df["erorrs"] * 2
    df.sort_values(by=["importance"], inplace=True, ascending=True)

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("importance", title="Relative importance (%)"),
            y=alt.Y("label", title=None, sort="-x", axis=alt.Axis(labelLimit=200)),
        )
        .properties(title="Variable importances")
    )

    error_bars = (
        alt.Chart(df)
        .mark_rule()
        .encode(
            y=alt.Y("label:N", title=None, sort="-x"),
            x=alt.X("low:Q"),
            x2=alt.X2("high:Q"),
            color=alt.value("white"),
            size=alt.value(4),
        )
    )

    return chart + error_bars
