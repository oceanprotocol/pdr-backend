from datetime import datetime
from typing import List

from enforce_typing import enforce_types
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import DecomposeResult, seasonal_decompose

from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
def pdr_seasonal_decompose(timeframe: ArgTimeframe, y_values) -> DecomposeResult:
    """
    @description
      Wraps statsmodels' seasonal_decompose() with predictoor-specific inputs

    @arguments
       timeframe -- time interval between x-values. ArgTimeframe('5m')
       y_values -- array-like -- [sample_i] : y_value_float
    """
    # preconditions
    assert len(y_values.shape) == 1, "y_values must be 1d array"

    # https://stackoverflow.com/questions/60017052/decompose-for-time-series-valueerror-you-must-specify-a-period-or-x-must-be
    s = timeframe.timeframe_str
    if s == "5m":
        period = 288  # 288 5min epochs per day
    elif s == "1h":
        period = 24  # 24 1h epochs per day
    else:
        raise ValueError(s)

    result = seasonal_decompose(y_values, period=period)
    return result


class SeasonalPlotdata:
    """Simple class to manage many inputs going to plot_seasonal."""

    @enforce_types
    def __init__(
        self,
        start_time: UnixTimeMs,
        timeframe: ArgTimeframe,
        decompose_result: DecomposeResult,
    ):
        """
        @arguments
          start_time -- x-value #0
          timeframe -- time interval between x-values. ArgTimeframe('5m')
          decompose_result -- has attributes (all array-like)
            observed - The data series that has been decomposed = y_values
            seasonal - The seasonal component of the data series.
            trend - The trend component of the data series.
            resid - The residual component of the data series.
            (weights - The weights used to reduce outlier influence.)
        """
        self.start_time = start_time
        self.timeframe = timeframe
        self.decompose_result = decompose_result

    @property
    def dr(self) -> DecomposeResult:
        """@description -- alias for decompose_result"""
        return self.decompose_result

    @property
    def N(self) -> int:
        """@return -- number of samples"""
        return self.dr.observed.shape[0]

    @property
    def x_ut(self) -> List[UnixTimeMs]:
        """@return -- x-values in unix time (ms)"""
        s = self.timeframe.timeframe_str
        if s == "5m":
            ms_per_5m = 300000
            uts = [self.start_time + i * ms_per_5m for i in range(self.N)]
        elif s == "1h":
            ms_per_1h = 3600000
            uts = [self.start_time + i * ms_per_1h for i in range(self.N)]
        else:
            raise ValueError(s)
        return [UnixTimeMs(ut) for ut in uts]

    @property
    def x_dt(self) -> List[datetime]:
        """@return - x-values in datetime object"""
        return [ut.to_dt() for ut in self.x_ut]


@enforce_types
def plot_seasonal(seasonal_plotdata: SeasonalPlotdata):
    """
    @description
      Plot seasonal decomposition of the feed, via 4 figures
      1. observed feed
      2. trend
      3. seasonal
      4. residual
    """
    d = seasonal_plotdata
    x = d.x_dt

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.01)

    # subplot 1: observed
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.observed,
            mode="lines",
            line={"color": "black", "width": 1},
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
            line={"color": "blue", "width": 1},
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
            line={"color": "green", "width": 1},
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
            line={"color": "red", "width": 1},
        ),
        row=4,
        col=1,
    )
    fig.update_yaxes(title_text="Residual", row=4, col=1)
    fig.update_xaxes(title_text="Time", row=4, col=1)

    # global
    minor = {"ticks": "inside", "showgrid": True}
    for row in [1, 2, 3, 4]:
        fig.update_yaxes(minor=minor, row=row, col=1)
        fig.update_xaxes(minor=minor, row=row, col=1)
    fig.update_layout(title_text="Seasonal decomposition", showlegend=False)
    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=15)

    return fig
