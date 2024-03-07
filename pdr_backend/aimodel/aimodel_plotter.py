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
    xranges=None,
    fancy_title: bool = False,
    legend_loc: str = "lower right",
):
    """
    @description
      Plot the model response in a contour plot.
      And overlay X-data. (Training data or otherwise.)
      Only relevant when the model has 2-d input.

    @arguments
      aimodel_plotdata -- holds:
        model -- Aimodel
        X_train -- array [sample_i][dim_i]:floatval -- trn model inputs (or other)
        ytrue_train -- array [sample_i]:boolval -- trn model outputs (or other)
        colnames -- list [dim_i]:X_column_name
      fig_ax -- None or (fig, ax) to easily embed into existing plot
      xranges -- None or (x0_min, x0_max, x1_min, x1_max) -- plot boundaries
      fancy_title -- should title have model accuracy info?
      legend_loc -- eg "upper left"
    """
    d = aimodel_plotdata
    (model, X, ytrue, colnames) = d.model, d.X_train, d.ytrue_train, d.colnames
    
    assert X.shape[1] == 2, "only relevant for 2-d input"
    
    assert len(colnames) == 2
    labels = tuple(colnames) # (x0 axis label, x1 axis label)    

    if xranges is None:
        x0_min, x0_max = min(X[:, 0]), max(X[:, 0])
        x1_min, x1_max = min(X[:, 1]), max(X[:, 1])
    else:
        x0_min, x0_max, x1_min, x1_max = xranges

    if fig_ax is None:
        fig, ax = plt.subplots()
    else:
        fig, ax = fig_ax
        ax.cla()  # clear axis

    feature_x = np.linspace(x0_min, x0_max, 200)
    feature_y = np.linspace(x1_min, x1_max, 200)
    dim0, dim1 = np.meshgrid(feature_x, feature_y)
    mesh_df0, mesh_df1 = dim0.ravel(), dim1.ravel()
    mesh_df = np.array([mesh_df0, mesh_df1]).T
    Z = model.predict_ptrue(mesh_df).reshape(dim1.shape)
    ax.contourf(dim0, dim1, Z, levels=25, cmap=cm.RdBu)  # type: ignore[attr-defined]

    ytrue_hat = model.predict_true(X)
    correct = ytrue_hat == ytrue
    wrong = np.invert(correct)
    ax.scatter(X[:, 0][wrong], X[:, 1][wrong], s=40, c="yellow", label="wrong")

    yfalse = np.invert(ytrue)
    ax.scatter(X[:, 0][ytrue], X[:, 1][ytrue], s=5, c="c", label="true")
    ax.scatter(X[:, 0][yfalse], X[:, 1][yfalse], s=5, c="r", label="false")

    n, n_correct, n_wrong = len(correct), sum(correct), sum(wrong)
    if fancy_title:
        ax.set_title(
            "Contours = model response. "
            f" {n_correct}/{n} = {n_correct/n*100:.2f}% correct"
            f", ie {n_wrong}/{n} = {n_wrong/n*100:.2f}% wrong"
        )
    else:
        ax.set_title("Contours = model response")

    ax.set_xlabel(labels[0])
    ax.set_ylabel(labels[1])

    HEIGHT = 9  # magic number
    WIDTH = HEIGHT
    fig.set_size_inches(WIDTH, HEIGHT)

    ax.legend(loc=legend_loc)
    plt.show()
