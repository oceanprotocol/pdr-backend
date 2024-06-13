from enforce_typing import enforce_types
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pdr_backend.statutil.dist_plotdata import DistPlotdata, DistPlotdataFactory


@enforce_types
def plot_dist(x, show_pdf: bool, show_cdf: bool, show_nq: bool):
    d: DistPlotdata = DistPlotdataFactory.build(x)
    fig = make_subplots(rows=sum([show_pdf, show_cdf, show_nq]), cols=1)
    row = 1
    if show_pdf:
        add_pdf(fig, d, row, 1)
        row += 1
    if show_cdf:
        add_cdf(fig, d, row, 1)
        row += 1
    if show_nq:
        add_nq(fig, d, row, 1)
    return fig


@enforce_types
def add_pdf(fig, d: DistPlotdata, row: int, col: int):

    fig.add_traces(
        [
            # 1d scatterplot of points
            go.Scatter(
                x=d.x,
                y=-d.y_jitter * 0.25 - 0.01,
                mode="markers",
                marker={"color": "black", "size": 2},
                name="raw data",
            ),
            # histogram
            go.Bar(
                x=d.bins,
                y=d.counts,
                width=[d.bar_width] * len(d.bins),
                marker_color=["grey"] * len(d.bins),
                showlegend=False,
                # name="raw data counted",
            ),
            # gaussian estimate of pdf
            go.Scatter(
                x=d.x_mesh,
                y=d.ypdf_normal_mesh,
                mode="lines",
                line={"color": "blue", "width": 2},
                name="gaussian est",
            ),
            # kde estimate of pdf
            go.Scatter(
                x=d.x_mesh,
                y=d.ypdf_kde_mesh,
                mode="lines",
                line={"color": "orange", "dash": "dot", "width": 2},
                name="kde est",
            ),
        ],
        rows=[row] * 4,
        cols=[col] * 4,
    )
    fig.update_yaxes(title="probability density (pdf)", row=row, col=col)


@enforce_types
def add_cdf(fig, d: DistPlotdata, row: int, col: int):

    fig.add_traces(
        [
            # 1d scatterplot of points
            go.Scatter(
                x=d.x,
                y=-d.y_jitter * 0.25 - 0.01,
                mode="markers",
                marker={"color": "black", "size": 2},
                showlegend=False,
                # name="raw data"
            ),
            # raw data cdf
            go.Scatter(
                x=d.x,
                y=d.ycdf_raw,
                mode="lines",
                line={"color": "grey", "width": 2},
                # showlegend=False,
                name="raw data counted",
            ),
            # gaussian estimate of cdf
            go.Scatter(
                x=d.x_mesh,
                y=d.ycdf_normal_mesh,
                mode="lines",
                line={"color": "blue", "width": 2},
                showlegend=False,
                # name="gaussian est",
            ),
            # kde estimate of cdf
            go.Scatter(
                x=d.x_mesh,
                y=d.ycdf_kde_mesh,
                mode="lines",
                line={"color": "orange", "dash": "dot", "width": 2},
                showlegend=False,
                # name="kde est",
            ),
        ],
        rows=[row] * 4,
        cols=[col] * 4,
    )
    fig.update_yaxes(title="cumulative density (cdf)", row=row, col=col)


@enforce_types
def add_nq(fig, d: DistPlotdata, row: int, col: int):
    xnq_raw, ynq_raw = _remove_extremey(d.x, d.ynq_raw, -4, 4)
    xnq_normal, ynq_normal = _remove_extremey(d.x_mesh, d.ynq_normal_mesh, -4, 4)
    xnq_kde, ynq_kde = _remove_extremey(d.x_mesh, d.ynq_kde_mesh, -4, 4)

    fig.add_traces(
        [
            # 1d scatterplot of points
            go.Scatter(
                x=d.x,
                y=-4 - 2 * d.y_jitter,
                mode="markers",
                marker={"color": "black", "size": 2},
                showlegend=False,
                # name="raw data"
            ),
            # raw data nq
            go.Scatter(
                x=xnq_raw,
                y=ynq_raw,
                mode="lines",
                line={"color": "grey", "width": 2},
                showlegend=False,
                # name="raw data counted"
            ),
            # gaussian estimate of nq
            go.Scatter(
                x=xnq_normal,
                y=ynq_normal,
                mode="lines",
                line={"color": "blue", "width": 2},
                showlegend=False,
                # name="gaussian est",
            ),
            # kde estimate of nq
            go.Scatter(
                x=xnq_kde,
                y=ynq_kde,
                mode="lines",
                line={"color": "orange", "dash": "dot", "width": 2},
                showlegend=False,
                # name="kde est",
            ),
        ],
        rows=[row] * 4,
        cols=[col] * 4,
    )
    fig.update_xaxes(title="residual (= actual - predicted)", row=row, col=col)
    fig.update_yaxes(title="normal quantile (nq)", row=row, col=col)
    fig.update_yaxes(minallowed=-6, maxallowed=+4, row=row, col=col)


@enforce_types
def _remove_extremey(x, y, min_y, max_y):
    x2, y2 = [], []
    for xi, yi in zip(x, y):
        if min_y <= yi <= max_y:
            x2.append(xi)
            y2.append(yi)
    return x2, y2
