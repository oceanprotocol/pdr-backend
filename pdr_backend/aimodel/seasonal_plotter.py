from enforce_typing import enforce_types
import plotly.graph_objects as go
from pdr_backend.aimodel.seasonal import SeasonalPlotdata

colors = ["black", "blue", "green", "red"]
minor = {"ticks": "inside", "showgrid": True}


@enforce_types
def plot_relative_energies(seasonal_plotdata: SeasonalPlotdata):
    d = seasonal_plotdata

    signal_names = d.dr.signal_names

    fig = go.Figure()

    # subplot 1: relative energies
    fig.add_trace(
        go.Bar(
            x=signal_names,
            y=d.dr.relative_energy,
            marker_color=colors,
            hoverinfo="x+y",
            width=0.25,
        )
    )
    fig.update_layout(
        title={
            "text": "Seasonal Decomp.",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        margin=dict(l=5, r=5, t=50, b=0),
    )
    fig.update_yaxes(title_text="Rel energy", minor=minor)
    fig.update_xaxes(minor=minor)
    return fig


@enforce_types
def plot_observed(seasonal_plotdata: SeasonalPlotdata):
    d = seasonal_plotdata
    x = d.x_dt

    fig = go.Figure()

    # subplot 1: relative energies
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.observed,
            mode="lines",
            line={"color": "black", "width": 1},
        ),
    )
    fig.update_yaxes(title_text="Obseved", minor=minor)
    fig.update_xaxes(minor=minor)
    fig.update_layout(margin=dict(l=5, r=5, t=20, b=0))
    return fig


@enforce_types
def plot_trend(seasonal_plotdata: SeasonalPlotdata):
    d = seasonal_plotdata
    x = d.x_dt

    fig = go.Figure()

    # subplot 1: relative energies
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.observed,
            mode="lines",
            line={"color": "blue", "width": 1},
        )
    )
    fig.update_yaxes(title_text="Trend", minor=minor)
    fig.update_xaxes(minor=minor)
    fig.update_layout(margin=dict(l=5, r=5, t=20, b=0))
    return fig


@enforce_types
def plot_seasonal(seasonal_plotdata: SeasonalPlotdata):
    d = seasonal_plotdata
    x = d.x_dt

    fig = go.Figure()

    # subplot 1: relative energies
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.observed,
            mode="lines",
            line={"color": "green", "width": 1},
        )
    )
    fig.update_yaxes(title_text="Seasonal", minor=minor)
    fig.update_xaxes(minor=minor)
    fig.update_layout(margin=dict(l=5, r=5, t=20, b=0))
    return fig


@enforce_types
def plot_residual(seasonal_plotdata: SeasonalPlotdata):
    d = seasonal_plotdata
    x = d.x_dt

    fig = go.Figure()

    # subplot 1: relative energies
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.observed,
            mode="lines",
            line={"color": "red", "width": 1},
        )
    )
    fig.update_yaxes(title_text="Resid", minor=minor)
    fig.update_xaxes(minor=minor)
    fig.update_layout(margin=dict(l=5, r=5, t=20, b=0))
    return fig
