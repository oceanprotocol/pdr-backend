from enforce_typing import enforce_types
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import DecomposeResult, seasonal_decompose

from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.util.time_types import UnixTimeMs

@enforce_types
def pdr_seasonal_decompose(timeframe: ArgTimeframe, y_values) \
        -> DecomposeResult:
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
        period = 288 # 288 5min epochs per day
    elif s == "1h":
        period = 24 # 24 1h epochs per day
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
        decompose_result: DecomposeResult
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
    def x(self) -> np.ndarray:
        """@return -- x-values = timestamps (ms)"""
        st = self.start_time
        fin = st + self.N
        return np.arange(self.start_time, self.start_time + self.N)

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

    fig = make_subplots(rows=4, cols=1)
    fig.add_trace(
        go.Scatter(
            x=d.x,
            y=d.dr.observed,
            mode="lines",
            line={"color": "blue", "width": 1},
        ), row=1, col=1,
    )
    fig.update_yaxes(title_text="Observed", row=1, col=1)

    
    fig.add_trace(
        go.Scatter(
            x=d.x,
            y=d.dr.trend,
            mode="lines",
            line={"color": "red", "width": 1},
        ), row=2, col=1,
    )
    fig.update_yaxes(title_text="Trend", row=1, col=1)

    
    fig.add_trace(
        go.Scatter(
            x=d.x,
            y=d.dr.seasonal,
            mode="lines",
            line={"color": "green", "width": 1},
        ), row=3, col=1,
    )
    fig.update_yaxes(title_text="Seasonal", row=1, col=1)

    
    fig.add_trace(
        go.Scatter(
            x=d.x,
            y=d.dr.resid,
            mode="lines",
            line={"color": "black", "width": 1},
        ), row=4, col=1,
    )
    fig.update_yaxes(title_text="Residual", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=4, col=1)

    fig.update_layout(
        height=800, width=800, title_text="Seasonal decomposition",
    )

    return fig

