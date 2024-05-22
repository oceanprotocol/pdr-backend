from enforce_typing import enforce_types
from plotly.subplots import make_subplots
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
    fig.update_yaxes(minor=minor)
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
    fig.update_yaxes(minor=minor)
    fig.update_xaxes(minor=minor)
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
            line={"color": "black", "width": 1},
        )
    )
    fig.update_yaxes(minor=minor)
    fig.update_xaxes(minor=minor)
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
            line={"color": "black", "width": 1},
        )
    )
    fig.update_yaxes(minor=minor)
    fig.update_xaxes(minor=minor)
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
            line={"color": "black", "width": 1},
        )
    )
    fig.update_yaxes(minor=minor)
    fig.update_xaxes(minor=minor)
    return fig
