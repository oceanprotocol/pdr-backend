from typing import Tuple

from enforce_typing import enforce_types
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

from pdr_backend.util.mathutil import classif_acc

@enforce_types
class Aimodel:
    
    def __init__(self, skm, scaler):
        self._skm = skm # sklearn model
        self._scaler = scaler

    def predict_true(self, X):
        """
        @description
          Classify each input sample, with lower fidelity: just True vs False
        
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs

        @return
          ytrue -- 1d array of [sample_i]:bool_value -- classifier model outputs
        """
        # We explicitly don't call skm.predict() here, because it's
        #   inconsistent with predict_proba() for svc and maybe others.
        # Rather, draw on the probability output to guarantee consistency.
        yptrue = self.predict_ptrue(X)
        print(f"in predict_true(); yptrue[:10] = {yptrue[:10]}")
        ytrue = yptrue > 0.5
        return ytrue

    def predict_ptrue(self, X: np.ndarray) -> np.ndarray:
        """
        @description
          Classify each input sample, with higher fidelity: prob of being True
        
        @arguments
          X -- 2d array of [sample_i, var_i]:cont_value -- model inputs
        
        @return
          yptrue - 1d array of [sample_i]: prob_of_being_true -- model outputs
        """
        X = self._scaler.transform(X)
        T = self._skm.predict_proba(X) # [sample_i][class_i]
        N = T.shape[0]
        class_i = 1 # this is the class for "True"
        yptrue = np.array([T[i,class_i] for i in range(N)])
        return yptrue

@enforce_types
def plot_model(
        model: Aimodel,
        X: np.ndarray,
        ytrue: np.ndarray,
        labels: Tuple[str, str],
        fancy_title: bool,
        fig_ax = None,
        xranges = None,
):
    """
    @description
      Plot the model response in a contour plot.
      And overlay X-data. (Training data or otherwise.)
      Only relevant when the model has 2-d input.

    @arguments
      model
      X -- [sample_i][dim_i]:floatval -- training model inputs (or other)
      ytrue -- [sample_i]:boolval -- training model outputs (or other)
      labels -- (x0 axis label, x1 axis label)
      fig_ax -- None or (fig, ax) to easily embed into existing plot
      xranges -- None or (x0_min, x0_max, x1_min, x1_max) -- plot boundaries
    """
    assert X.shape[1] == 2, "only relevant for 2-d input"
    N = X.shape[1]

    x0_label, x1_labels = labels

    if xranges is None:
        x0_min, x0_max = min(X[:,0]), max(X[:,0])
        x1_min, x1_max = min(X[:,1]), max(X[:,1])
    else:
        x0_min, x0_max, x1_min, x1_max = xranges
        
    if fig_ax is None:
        fig, ax = plt.subplots()
    else:
        fig, ax = fig_ax
        ax.cla() # clear axis

    feature_x = np.linspace(x0_min, x0_max, 200)
    feature_y = np.linspace(x1_min, x1_max, 200)
    dim0, dim1 = np.meshgrid(feature_x, feature_y)
    mesh_df0, mesh_df1 = dim0.ravel(), dim1.ravel()
    mesh_df = np.array([mesh_df0, mesh_df1]).T
    Z = model.predict_ptrue(mesh_df).reshape(dim1.shape)
    ax.contourf(dim0, dim1, Z, levels=25, cmap=cm.RdBu)
    
    ytrue_hat = model.predict_true(X)
    correct = (ytrue_hat == ytrue)
    wrong = np.invert(correct)
    ax.scatter(X[:,0][wrong], X[:,1][wrong], s=40, c="yellow", label="wrong")

    yfalse = np.invert(ytrue)
    ax.scatter(X[:,0][ytrue], X[:,1][ytrue], s=5, c="c", label="true")
    ax.scatter(X[:,0][yfalse], X[:,1][yfalse], s=5, c="r", label="false")

    n, n_correct, n_wrong = len(correct), sum(correct), sum(wrong)
    if fancy_title:
        ax.set_title(
            "Contours = model response. "
            f" {n_correct}/{n} = {n_correct/n*100:.2f}% correct"
            f", ie {n_wrong}/{n} = {n_wrong/n*100:.2f}% wrong"
        )
    else:
        ax.set_title("Contours = model response")
    
    ax.set_xlabel("x0")
    ax.set_ylabel("x1")

    HEIGHT = 9  # magic number
    WIDTH = HEIGHT
    fig.set_size_inches(WIDTH, HEIGHT)

    ax.legend(loc="upper right")
    plt.show()

