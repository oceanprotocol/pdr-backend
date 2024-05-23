from enforce_typing import enforce_types
from plotly.subplots import make_subplots

from pdr_backend.aimodel.autocorrelation import (
    AutocorrelationPlotdata,
    _add_corr_traces,
)


@enforce_types
def plot_acf(autocorrelation_plotdata: AutocorrelationPlotdata):
    """
    @description
      Plot autocorrelation function (ACF)
    """
    d = autocorrelation_plotdata
    fig = make_subplots(rows=1, cols=1)

    _add_corr_traces(d.acf_results, fig, row=1)
    fig.update_xaxes(title_text="lag", row=1, col=1)

    # Set minor ticks
    minor = {"ticks": "inside", "showgrid": True}
    fig.update_yaxes(minor=minor, row=1, col=1)

    # Layout settings
    fig.update_layout(
        title={
            "text": "Autocorrelation (ACF)",
            "y": 0.96,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        margin={"l": 5, "r": 5, "t": 50, "b": 0},
        showlegend=False,
    )

    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=16)
    delta = 0.05 * d.max_lag
    fig.update_xaxes(range=[0 - delta, d.max_lag - delta])

    return fig


@enforce_types
def plot_pacf(autocorrelation_plotdata: AutocorrelationPlotdata):
    """
    @description
      Plot partial autocorrelation function (PACF)
    """
    d = autocorrelation_plotdata
    fig = make_subplots(rows=1, cols=1)

    _add_corr_traces(d.pacf_results, fig, row=1)
    fig.update_xaxes(title_text="lag", row=1, col=1)

    # Set minor ticks
    minor = {"ticks": "inside", "showgrid": True}
    fig.update_yaxes(minor=minor, row=1, col=1)

    # Layout settings
    fig.update_layout(
        title={
            "text": "Partial Autocorrelation (PACF)",
            "y": 0.96,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        margin={"l": 5, "r": 5, "t": 50, "b": 0},
        showlegend=False,
    )

    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=16)
    delta = 0.05 * d.max_lag
    fig.update_xaxes(range=[0 - delta, d.max_lag - delta])

    return fig
