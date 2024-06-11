from enforce_typing import enforce_types
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from scipy.special import ndtr


@enforce_types
def plot_pdf(x):
    fig = make_subplots(rows=1, cols=1)
    add_pdf(fig, x, 1, 1)
    return fig

@enforce_types
def plot_pdf_cdf_nq(x):
    fig = make_subplots(rows=3, cols=1)
    add_pdf(fig, x, 1, 1)
    add_cdf(fig, x, 2, 1)
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
    nbins = max(3, min(100, len(x)//5))
    counts, bins = np.histogram(x, bins=nbins)
    bins = 0.5 * (bins[:-1] + bins[1:])
    bar_width = bins[1] - bins[0]
    
    mean, std = np.mean(x), np.std(x)
    x_mesh = np.linspace(min(x) - std, max(x) + std, num=200)

    ypdf_normal_mesh = stats.norm.pdf(x_mesh, mean, std)
    
    kde_model = stats.gaussian_kde(x)
    ypdf_kde_mesh = kde_model.evaluate(x_mesh)

    max_est = max(max(ypdf_normal_mesh), max(ypdf_kde_mesh))
    ypdf_jitter = - _get_jitter(len(x)) * max_est * 0.25 - 0.01
    
    fig.add_traces(
        [
            # 1d scatterplot of points
            go.Scatter(
                x=x,
                y=ypdf_jitter,
                mode="markers",
                marker={"color": "black", "size": 2},
                name="raw data"
            ),
            
            # histogram
            go.Bar(
                x=bins,
                y=counts/max(counts)*max_est,
                width=[bar_width] * len(bins),
                marker_color=["grey"] * len(bins),
                showlegend=False,
                #name="raw data counted",
            ),

            # gaussian estimate of pdf
            go.Scatter(
                x=x_mesh,
                y=ypdf_normal_mesh,
                mode="lines",
                line={"color": "blue", "width":2},
                name="gaussian est",
            ),

            # kde estimate of pdf
            go.Scatter(
                x=x_mesh,
                y=ypdf_kde_mesh,
                mode="lines",
                line={"color": "orange", "dash":"dot", "width":2},
                name="kde est",
            ),
        ],
        rows=[row]*4,
        cols=[col]*4,
    )
    fig.update_yaxes(title="density", row=row, col=col)



@enforce_types
def add_cdf(fig, x, row: int, col: int, xaxis_title:str="x-value"):
    x = sorted(x)
    ycdf_raw = np.linspace(0.0, 1.0, len(x))
    
    mean, std = np.mean(x), np.std(x)
    x_mesh = np.linspace(min(x) - std, max(x) + std, num=200)

    ycdf_normal_mesh = stats.norm.cdf(x_mesh, mean, std)
    
    kde_model = stats.gaussian_kde(x)    
    ycdf_kde_mesh = [
        ndtr(np.ravel(x_item - kde_model.dataset) / kde_model.factor).mean()
        for x_item in x_mesh
    ]

    y_jitter = - _get_jitter(len(x)) * 0.25 - 0.01
    
    fig.add_traces(
        [
            # 1d scatterplot of points
            go.Scatter(
                x=x,
                y=y_jitter,
                mode="markers",
                marker={"color": "black", "size": 2},
                showlegend=False,
                #name="raw data"
            ),
            
            # raw data cdf
            go.Scatter(
                x=x,
                y=ycdf_raw,
                mode="lines",
                line={"color": "grey", "width": 2},
                #showlegend=False,
                name="raw data counted"
            ),

            # gaussian estimate of cdf
            go.Scatter(
                x=x_mesh,
                y=ycdf_normal_mesh,
                mode="lines",
                line={"color": "blue", "width":2},
                showlegend=False,
                #name="gaussian est",
            ),

            # kde estimate of cdf
            go.Scatter(
                x=x_mesh,
                y=ycdf_kde_mesh,
                mode="lines",
                line={"color": "orange", "dash":"dot", "width":2},
                showlegend=False,
                #name="kde est",
            ),
        ],
        rows=[row]*4,
        cols=[col]*4,
    )
    fig.update_yaxes(title="cumulative density", row=row, col=col)



    
J = np.array([], dtype=float)  # jitter


@enforce_types
def _get_jitter(N: int) -> np.ndarray:
    global J
    while J.shape[0] < N:
        J = np.append(J, np.random.rand())
    return J[:N]
