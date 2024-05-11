from datetime import datetime
from typing import List

from enforce_typing import enforce_types
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import DecomposeResult, seasonal_decompose

from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.util.mathutil import has_nan
from pdr_backend.util.time_types import UnixTimeMs


class SeasonalDecomposeResult:
    """
    @description
      Wraps statsmodels DecomposeResult with predictoor-specific goodies
    """

    @enforce_types
    def __init__(self, timeframe: ArgTimeframe, raw_dr: DecomposeResult):
        """
        @arguments
          timeframe -- time interval between x-values. ArgTimeframe('5m')
          raw_dr -- has attributes (all array-like)
            observed - The data series that has been decomposed = y_values
            seasonal - The seasonal component of the data series.
            trend - The trend component of the data series.
            resid - The residual component of the data series.
            (weights - The weights used to reduce outlier influence.)
        """
        # set values
        self.timeframe = timeframe
        self.signals = [
            raw_dr.observed,
            raw_dr.trend,
            raw_dr.seasonal,
            raw_dr.resid,
        ]
        self.signal_names = ["observed", "trend", "seasonal", "resid"]
        self._raw_dr = raw_dr

        # postconditions
        self.assert_no_nans()

    @property
    def observed(self) -> np.ndarray:
        return self._raw_dr.observed

    @property
    def seasonal(self) -> np.ndarray:
        return self._raw_dr.seasonal

    @property
    def trend(self) -> np.ndarray:
        return self._raw_dr.trend

    @property
    def resid(self) -> np.ndarray:
        return self._raw_dr.resid

    @property
    def relative_energy(self) -> np.ndarray:
        """
        @return -- relative energy of [observed, seasonal, trend, resid]
        where relative energy == stddev, normalized by stddev of observed
        """
        stds = np.array([np.std(signal) for signal in self.signals])
        std_observed = stds[0]
        return stds / std_observed

    @enforce_types
    def assert_no_nans(self):
        for i, signal in enumerate(self.signals):
            assert not has_nan(signal), f"{self.signal_names[i]} has a nan"


class SeasonalDecomposeFactory:

    @classmethod
    def build(cls, timeframe: ArgTimeframe, y_values) -> SeasonalDecomposeResult:
        """
        @description
          Wraps statsmodels seasonal_decompose() with pdr-specific inputs,
          and a pdr-specific output

        @arguments
           timeframe -- time interval between x-values. ArgTimeframe('5m')
           y_values -- array-like -- [sample_i] : y_value_float
        """
        # preconditions
        assert len(y_values.shape) == 1, "y_values must be 1d array"

        period = cls._timeframe_to_period(timeframe)
        raw_dr = seasonal_decompose(y_values, period=period, extrapolate_trend=1)
        dr = SeasonalDecomposeResult(timeframe, raw_dr)

        return dr

    @staticmethod
    def _timeframe_to_period(timeframe: ArgTimeframe) -> int:
        """Given a timeframe, return the # epochs in a seasonal period
        https://stackoverflow.com/questions/60017052/decompose-for-time-series-valueerror-you-must-specify-a-period-or-x-must-be
        """
        s = timeframe.timeframe_str
        if s == "5m":
            return 288  # 288 5min epochs per day
        if s == "1h":
            return 24  # 24 1h epochs per day
        raise ValueError(s)


class SeasonalPlotdata:
    """Simple class to manage many inputs going to plot_seasonal."""

    @enforce_types
    def __init__(
        self,
        start_time: UnixTimeMs,
        decompose_result: SeasonalDecomposeResult,
    ):
        """
        @arguments
          start_time -- x-value #0
          decompose_result
        """
        self.start_time = start_time
        self.decompose_result = decompose_result

    @property
    def dr(self) -> SeasonalDecomposeResult:
        """@description -- alias for decompose_result"""
        return self.decompose_result

    @property
    def N(self) -> int:
        """@return -- number of samples"""
        return self.dr.observed.shape[0]

    @property
    def x_ut(self) -> List[UnixTimeMs]:
        """@return -- x-values in unix time (ms)"""
        s = self.dr.timeframe.timeframe_str
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
      Plot seasonal decomposition of the feed, via 5 figures
      1. relative energies of 2-5
      2. observed feed
      3. trend
      4. seasonal
      5. residual
    """
    d = seasonal_plotdata
    x = d.x_dt

    signal_names = d.dr.signal_names  # ["observed", ...]
    colors = ["black", "blue", "green", "red"]
    colormap = dict(zip(signal_names, colors))

    fig = make_subplots(rows=5, cols=1, vertical_spacing=0.02)

    # subplot 1: relative energies
    fig.add_trace(
        go.Bar(
            x=signal_names,
            y=d.dr.relative_energy,
            marker_color=colors,
            hoverinfo="x+y",
            width=0.25,
        ),
        row=1,
        col=1,
    )
    fig.update_yaxes(title_text="relative energy", row=1, col=1)

    # subplot 2: observed
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.observed,
            mode="lines",
            line={"color": colormap["observed"], "width": 1},
        ),
        row=2,
        col=1,
    )
    fig.update_yaxes(title_text="observed", row=2, col=1)

    # subplot 3: trend
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.trend,
            mode="lines",
            line={"color": colormap["trend"], "width": 1},
        ),
        row=3,
        col=1,
    )
    fig.update_yaxes(title_text="trend", row=3, col=1)

    # subplot 4: seasonal
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.seasonal,
            mode="lines",
            line={"color": colormap["seasonal"], "width": 1},
        ),
        row=4,
        col=1,
    )
    fig.update_yaxes(title_text="seasonal", row=4, col=1)

    # subplot 5: residual
    fig.add_trace(
        go.Scatter(
            x=x,
            y=d.dr.resid,
            mode="lines",
            line={"color": colormap["resid"], "width": 1},
        ),
        row=5,
        col=1,
    )
    fig.update_yaxes(title_text="resid", row=5, col=1)
    fig.update_xaxes(title_text="time", row=5, col=1)

    # global: set minor ticks
    minor = {"ticks": "inside", "showgrid": True}
    fig.update_yaxes(minor=minor, row=1, col=1)
    for row in [2, 3, 4, 5]:
        fig.update_yaxes(minor=minor, row=row, col=1)
        fig.update_xaxes(minor=minor, row=row, col=1)

    # global: share x-axes of subplots 2-5
    fig.update_layout(
        {
            "xaxis": {"matches": None},
            "xaxis2": {"matches": "x", "showticklabels": True},
            "xaxis3": {"matches": "x", "showticklabels": False},
            "xaxis4": {"matches": "x", "showticklabels": False},
            "xaxis5": {"matches": "x", "showticklabels": True},
        }
    )

    # global: other
    fig.update_layout(
        title_text="Seasonal decomposition",
        showlegend=False,
    )
    fig.update_yaxes(nticks=8)
    fig.update_xaxes(nticks=15)

    return fig
