from typing import Tuple

from enforce_typing import enforce_types
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata


@enforce_types
def plot_aimodel_contour(
        aimodel_plotdata: AimodelPlotdata,
        fig_ax=None,
        legend_loc: str = "lower right",
):
    """
    @description
      Plot the model response in a contour plot.
      And overlay X-data. (Training data or otherwise.)
      If the model has >2 vars, it plots the 2 most important vars.

    @arguments
      aimodel_plotdata -- holds:
        model -- Aimodel
        X_train -- array [sample_i][dim_i]:floatval -- trn model inputs (or other)
        ytrue_train -- array [sample_i]:boolval -- trn model outputs (or other)
        colnames -- list [dim_i]:X_column_name
        slicing_x -- arrat [dim_i]:floatval - when >2 dims, plot about this pt
      fig_ax -- None or (fig, ax) to easily embed into existing plot
      legend_loc -- eg "upper left"
    """
    # aimodel data
    d = aimodel_plotdata
    (model, X, ytrue, colnames, slicing_x) = \
        d.model, d.X_train, d.ytrue_train, d.colnames, d.slicing_x

    # take 2 most impt vars
    nvars = X.shape[1]
    assert nvars > 0
    if nvars == 1:
        impt_I = [0, 0]
    elif nvars == 2:
        impt_I = [0, 1]
    else:
        impt_I = np.argsort(model.importance_per_var())[:2]
    impt_X = X[:,impt_I]
    impt_colnames = [colnames[i] for i in impt_I]

    # calc min/max
    x0_min, x0_max = min(impt_X[:, 0]), max(impt_X[:, 0])
    x1_min, x1_max = min(impt_X[:, 1]), max(impt_X[:, 1])

    # start fig
    if fig_ax is None:
        fig, ax = plt.subplots()
    else:
        fig, ax = fig_ax
        ax.cla()  # clear axis

    # calc mesh_X = uniform grid across two most important dimensions,
    #  and every other dimension i has value slicing_x[i]
    feature_x = np.linspace(x0_min, x0_max, 200)
    feature_y = np.linspace(x1_min, x1_max, 200)
    dim0, dim1 = np.meshgrid(feature_x, feature_y)
    mesh_0, mesh_1 = dim0.ravel(), dim1.ravel()
    mesh_impt_X = np.array([mesh_0, mesh_1]).T # [sample_i][impt_dim_i]
    slicing_X = np.reshape(slicing_x, (1, nvars)) # [0][dim_i]
    mesh_N = mesh_impt_X.shape[0]
    mesh_X = np.repeat(slicing_X, mesh_N, axis=0) # [sample_i][dim_i]
    mesh_X[:,impt_I] = mesh_impt_X

    # calc Z = model operating on mesh_X
    Z = model.predict_ptrue(mesh_X).reshape(dim1.shape)

    # contour plot on Z
    ax.contourf(dim0, dim1, Z, levels=25, cmap=cm.RdBu)  # type: ignore[attr-defined]

    ytrue_hat = model.predict_true(X)
    correct = ytrue_hat == ytrue
    wrong = np.invert(correct)

    # scatterplots: cyan=training_T, red=training_F, yellow_outline=misclassify
    ax.scatter(impt_X[:, 0][wrong], impt_X[:, 1][wrong], s=40, c="yellow", label="wrong")

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
