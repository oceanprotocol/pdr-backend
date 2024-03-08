from typing import Dict, List, Tuple

from enforce_typing import enforce_types
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata


@enforce_types
def plot_aimodel_response(
    aimodel_plotdata: AimodelPlotdata,
    fig_ax=None,
    legend_loc: str = "lower right",
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
        _plot_aimodel_lineplot(aimodel_plotdata, fig_ax)
    else:
        _plot_aimodel_contour(aimodel_plotdata, fig_ax, legend_loc)


J = np.array([], dtype=float)  # jitter


@enforce_types
def _plot_aimodel_lineplot(aimodel_plotdata: AimodelPlotdata, fig_ax):
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

    # start fig
    if fig_ax is None:
        fig, ax = plt.subplots()
    else:
        fig, ax = fig_ax
        ax.cla()  # clear axis

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
    for i, xi in enumerate(x[wrong]):
        label = "wrong" if i == 0 else None
        ax.plot([xi, xi], [0.0, 1.0], linewidth=1, c="yellow", label=label)

    # line plot: model response surface
    ax.plot(mesh_x, z, c="k", label="model prob(true)")

    # scatterplots: cyan=training_T, red=training_F
    global J
    while J.shape[0] < N:
        J = np.append(J, np.random.rand() * 0.05)
    yfalse = np.invert(ytrue)
    y1 = ytrue[ytrue] - J[ytrue] + 0.025
    y2 = ytrue[yfalse] + J[yfalse] - 0.025
    ax.scatter(x[ytrue], y1, s=2, c="c", label="trn data true")
    ax.scatter(x[yfalse], y2, s=2, c="r", label="trn data false")

    # labels
    ax.set_title(f"Prob(true) vs {d.colnames[0]}")
    ax.set_xlabel(d.colnames[0])
    ax.set_ylabel("Prob(true)")

    HEIGHT = 9  # magic number
    WIDTH = HEIGHT
    fig.set_size_inches(WIDTH, HEIGHT)

    ax.legend(loc="upper left")
    plt.show()


@enforce_types
def _plot_aimodel_contour(
    aimodel_plotdata: AimodelPlotdata,
    fig_ax,
    legend_loc,
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

    # start fig
    if fig_ax is None:
        fig, ax = plt.subplots()
    else:
        fig, ax = fig_ax
        ax.cla()  # clear axis

    # take 2 most impt vars
    nvars = X.shape[1]
    assert nvars > 1
    if nvars == 1:
        impt_I = [0, 0]
    elif nvars == 2:
        impt_I = [0, 1]
    else:
        impt_I = np.argsort(d.model.importance_per_var())[::-1][:2]
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

    # contour plot: model response surface
    ax.contourf(dim0, dim1, Z, levels=25, cmap=cm.RdBu)  # type: ignore[attr-defined]

    # scatterplots: cyan=training_T, red=training_F, yellow_outline=misclassify
    ytrue_hat = d.model.predict_true(X)
    correct = ytrue_hat == ytrue
    wrong = np.invert(correct)

    ax.scatter(
        impt_X[:, 0][wrong], impt_X[:, 1][wrong], s=40, c="yellow", label="wrong"
    )

    yfalse = np.invert(ytrue)
    ax.scatter(impt_X[:, 0][ytrue], impt_X[:, 1][ytrue], s=5, c="c", label="true")
    ax.scatter(impt_X[:, 0][yfalse], impt_X[:, 1][yfalse], s=5, c="r", label="false")

    ax.set_title("Contours = model response")
    ax.set_xlabel(impt_colnames[0])
    ax.set_ylabel(impt_colnames[1])

    HEIGHT = 9  # magic number
    WIDTH = HEIGHT
    fig.set_size_inches(WIDTH, HEIGHT)

    ax.legend(loc=legend_loc)
    plt.show()


@enforce_types
def plot_aimodel_varimps(
        varnames: List[str],
        imps_tup: tuple,
        fig_ax=None,
):
    """
    @description
      Bar plot showing rel importance of vars
      Including 95% confidence intervals (2.0 stddevs)

    @arguments
      varnames -- variable names
      imps_tup -- tuple of (imps_avg, imps_stddev)
      fig_ax -- None or (fig, ax) to easily embed into existing plot
    """
    imps_avg, imps_stddev = imps_tup

    # re-order in descending imps_avg
    I = np.argsort(imps_avg)[::-1]
    imps_avg = imps_avg[I]
    imps_stddev = imps_stddev[I]
    varnames = [varnames[i] for i in I]
    
    # start fig
    if fig_ax is None:
        fig, ax = plt.subplots()
    else:
        fig, ax = fig_ax
        ax.cla()  # clear axis

    # plot
    y_pos = np.arange(len(varnames))
    error = np.random.rand(len(varnames))

    ax.barh(y_pos, imps_avg, xerr=imps_stddev*2, align="center")
    ax.set_xlim(left=0.0)
    ax.set_yticks(y_pos, labels=varnames)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel("Rel importance")
    ax.set_title("Variable importances")


    HEIGHT = 9  # magic number
    WIDTH = HEIGHT
    fig.set_size_inches(WIDTH, HEIGHT)

    plt.show()
