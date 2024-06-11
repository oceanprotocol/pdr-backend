from enforce_typing import enforce_types
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats


@enforce_types
def plot_pdf(x):
    fig = make_subplots(rows=1, cols=1)
    add_pdf(fig, x, 1, 1)
    return fig

@enforce_types
def plot_pdf_cdf_nq(x):
    fig = make_subplots(rows=3, cols=1)
    add_pdf(fig, x, 1, 1)
    #add_cdf(fig, x, 2, 1) # FIXME un-comment
    #add_nq(fig, x, 3, 1) # FIXME un-comment
    return fig

@enforce_types
def plot_pdf_nq(x):
    fig = make_subplots(rows=3, cols=1)
    add_pdf(fig, x, 1, 1)
    #add_nq(fig, x, 3, 1) # FIXME un-comment
    return fig


@enforce_types
def add_pdf(fig, x, row: int, col: int, xaxis_title:str="x-value"):    
    std = np.std(x)
    x_mesh = np.linspace(min(x) - std, max(x) + std, num=200)
    
    kde_model = stats.gaussian_kde(x)
    kde_mesh = kde_model.evaluate(x_mesh)
    y_kde_mesh = kde_mesh / max(kde_mesh) # normalized to max=1.0
    
    fig.add_traces(
        [
            # 1d scatterplot of points
            go.Scatter(
                x=x,
                y=-0.1 * _get_jitter(len(x)),
                mode="markers",
                marker={"color": "black", "size": 2},
                name="raw"
            ),

            # kde estimate
            go.Scatter(
                x=x_mesh,
                y=y_kde_mesh,
                mode="lines",
                line={"color": "blue"},
                name="kde",
            ),

            # to add: normal distribution
        ],
        rows=[row]*2,
        cols=[col]*2,
    )
    fig.update_yaxes(title="density", row=row, col=col)

J = np.array([], dtype=float)  # jitter


@enforce_types
def _get_jitter(N: int) -> np.ndarray:
    global J
    while J.shape[0] < N:
        J = np.append(J, np.random.rand())
    return J[:N]
