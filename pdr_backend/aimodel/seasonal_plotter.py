from enforce_typing import enforce_types
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pdr_backend.aimodel.seasonal import SeasonalPlotdata

colors = ["black", "blue", "green", "red"]
minor = {"ticks": "inside", "showgrid": True}


@enforce_types
def plot_relative_energies(seasonal_plotdata: SeasonalPlotdata):
    d = seasonal_plotdata

    signal_names = d.dr.signal_names

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=signal_names,
            y=d.dr.relative_energy,
            marker_color=colors,
            hoverinfo="x+y",
            width=0.25,
        )
    )
    fig.update_layout(margin={"l": 20, "r": 20, "t": 20, "b": 0})
    fig.update_yaxes(title_text="Rel energy", minor=minor, tickformat=".4f")
    fig.update_xaxes(minor=minor)
    return fig


def create_seasonal_plot(seasonal_plotdata: SeasonalPlotdata):
    d = seasonal_plotdata
    x = d.x_dt

    signal_names = d.dr.signal_names  # ["observed", ...]
    colormap = dict(zip(signal_names, colors))

    fig = make_subplots(rows=4, cols=1, vertical_spacing=0)

    # subplot 1: observed
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.observed,
            mode="lines",
            line={"color": colormap["observed"], "width": 1},
        ),
        row=1,
        col=1,
    )
    fig.update_yaxes(title_text="Observed", row=1, col=1)

    # subplot 2: trend
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.trend,
            mode="lines",
            line={"color": colormap["trend"], "width": 1},
        ),
        row=2,
        col=1,
    )
    fig.update_yaxes(title_text="Trend", row=2, col=1)

    # subplot 3: seasonal
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.seasonal,
            mode="lines",
            line={"color": colormap["seasonal"], "width": 1},
        ),
        row=3,
        col=1,
    )
    fig.update_yaxes(title_text="Seasonal", row=3, col=1)

    # subplot 4: residual
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.resid,
            mode="lines",
            line={"color": colormap["resid"], "width": 1},
        ),
        row=4,
        col=1,
    )
    fig.update_yaxes(title_text="Resid", row=4, col=1)
    fig.update_xaxes(title_text="time", row=4, col=1)

    fig.update_yaxes(minor=minor, row=1, col=1)
    for row in [1, 2, 3, 4]:
        fig.update_yaxes(minor=minor, row=row, col=1)
        fig.update_xaxes(minor=minor, row=row, col=1)

    # global: share x-axes of subplots 2-5
    fig.update_layout(
        {
            "xaxis1": {"matches": "x", "showticklabels": False},
            "xaxis2": {"matches": "x", "showticklabels": False},
            "xaxis3": {"matches": "x", "showticklabels": False},
            "xaxis4": {"matches": "x", "showticklabels": True},
        }
    )

    # global: other
    fig.update_layout(
        showlegend=False,
    )
    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=15)

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 20, "b": 0}, xaxis={"showticklabels": False}
    )

    return fig
