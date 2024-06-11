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
    mean, std = np.mean(x), np.std(x)
    x_mesh = np.linspace(min(x) - std, max(x) + std, num=200)

    y_gaussian_mesh = stats.norm.pdf(x_mesh, mean, std)
    
    kde_model = stats.gaussian_kde(x)
    y_kde_mesh = kde_model.evaluate(x_mesh)

    max_est = max(max(y_gaussian_mesh), max(y_kde_mesh))
    y_jitter = - _get_jitter(len(x)) * max_est * 0.25
    
    fig.add_traces(
        [
            # 1d scatterplot of points
            go.Scatter(
                x=x,
                y=y_jitter,
                mode="markers",
                marker={"color": "black", "size": 2},
                name="raw data"
            ),

            # gaussian estimate of pdf
            go.Scatter(
                x=x_mesh,
                y=y_gaussian_mesh,
                mode="lines",
                line={"color": "blue"},
                name="gaussian est",
            ),

            # kde estimate of pdf
            go.Scatter(
                x=x_mesh,
                y=y_kde_mesh,
                mode="lines",
                line={"color": "orange"},
                name="kde est",
            ),

            # to add: normal distribution
        ],
        rows=[row]*3,
        cols=[col]*3,
    )
    fig.update_yaxes(title="density", row=row, col=col)

J = np.array([], dtype=float)  # jitter


@enforce_types
def _get_jitter(N: int) -> np.ndarray:
    global J
    while J.shape[0] < N:
        J = np.append(J, np.random.rand())
    return J[:N]
