from datetime import datetime
from dash import Input, Output, State, html
import pandas as pd
from scipy import stats
import dash
import numpy as np
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.aimodel.dash_plots.view_elements import get_column_graphs
from pdr_backend.aimodel.autocorrelation import (
    AutocorrelationPlotdataFactory,
    AutocorrelationPlotdata,
)
from pdr_backend.aimodel.autocorrelation_plotter import (
    plot_acf,
    plot_pacf,
    get_transitions,
)
from pdr_backend.aimodel.seasonal import (
    SeasonalDecomposeFactory,
    SeasonalPlotdata,
)
from pdr_backend.aimodel.seasonal_plotter import (
    plot_relative_energies,
    plot_observed,
    plot_residual,
    plot_seasonal,
    plot_trend,
)
from pdr_backend.aimodel.dash_plots.util import (
    read_files_from_directory,
    filter_file_data_by_date,
)


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(Output("file-data", "data"), Input("data-folder", "data"))
    def read_from_file(data):
        files_dir = data
        data = read_files_from_directory(files_dir)
        return data

    @app.callback(
        Output("error-message", "children"),
        [
            Input("file-data", "data"),
        ],
    )
    def display_read_data_error(store_data):
        if store_data == {}:
            return html.H2(
                "No data found! Fetch ohlcv data before running the ARIMA plots."
            )
        return None

    @app.callback(
        Output("autocorelation_column", "children"),
        Output("seasonal_column", "children"),
        [
            Input("feed-dropdown", "value"),
            Input("date-picker-range", "start_date"),
            Input("date-picker-range", "end_date"),
            Input("transition-data", "data"),
        ],
        State("file-data", "data"),
    )
    # pylint: disable=unused-argument
    def create_charts(
        feed_data, date_picker_start_date, date_picker_end_date, transition, files_data
    ):
        if transition is None:
            return [], []
        nlags = 10
        do_boxcox = transition["BC"]
        differencing_order = transition["D"]

        files_data[feed_data] = filter_file_data_by_date(
            files_data[feed_data],
            datetime.strptime(date_picker_start_date, "%Y-%m-%d"),
            datetime.strptime(date_picker_end_date, "%Y-%m-%d"),
        )

        y = files_data[feed_data]["close_data"]

        # get data for autocorelation
        y = np.array(y)
        if do_boxcox:
            y, _ = stats.boxcox(y)
        for _ in range(differencing_order):
            y = y[1:] - y[:-1]

        data = AutocorrelationPlotdataFactory.build(y, nlags)
        assert isinstance(data, AutocorrelationPlotdata)

        if data is None:
            return dash.no_update

        # get data for seasonal
        y = files_data[feed_data]["close_data"]
        y = np.array(y)
        timestamp_str = files_data[feed_data]["timestamps"][0]
        st = UnixTimeMs(timestamp_str.timestamp() * 1000)
        t = ArgTimeframe(feed_data.split("_")[len(feed_data.split("_")) - 1])
        dr = SeasonalDecomposeFactory.build(t, y)

        plotdata = SeasonalPlotdata(st, dr)

        acf = plot_acf(data)
        pacf = plot_pacf(data)

        relativeEnergies = plot_relative_energies(plotdata)
        observed = plot_observed(plotdata)
        trend = plot_trend(plotdata)
        seasonal = plot_seasonal(plotdata)
        ressidual = plot_residual(plotdata)

        seasonal_charts = get_column_graphs(
            [
                {"fig": relativeEnergies, "graph_id": "relativeEnergies"},
                {"fig": observed, "graph_id": "observed"},
                {"fig": trend, "graph_id": "trend"},
                {"fig": seasonal, "graph_id": "seasonal"},
                {"fig": ressidual, "graph_id": "ressidual"},
            ]
        )

        autocorelation_charts = get_column_graphs(
            [
                {"fig": acf, "graph_id": "autocorelation"},
                {"fig": pacf, "graph_id": "pautocorelation"},
            ]
        )

        return autocorelation_charts, seasonal_charts

    @app.callback(
        Output("transition_column", "children"),
        [
            Input("transition_column", "id"),
            Input("date-picker-range", "start_date"),
            Input("date-picker-range", "end_date"),
            Input("feed-dropdown", "value"),
        ],
        State("file-data", "data"),
    )
    # pylint: disable=unused-argument
    def create_transition_chart(
        div, date_picker_start_date, date_picker_end_date, feed_data, files_data
    ):
        files_data[feed_data] = files_data[feed_data] = filter_file_data_by_date(
            files_data[feed_data],
            datetime.strptime(date_picker_start_date, "%Y-%m-%d"),
            datetime.strptime(date_picker_end_date, "%Y-%m-%d"),
        )
        figure = get_transitions(None, files_data[feed_data]["close_data"])
        transitions = get_column_graphs(
            [{"fig": figure, "graph_id": "transition_graph"}]
        )
        return html.Div(transitions)

    @app.callback(
        Output("transition_graph", "figure"),
        Output("transition-data", "data"),
        [Input("transition_graph", "clickData")],
        [State("transition_graph", "figure")],
    )
    def display_click_data(clickData, figure):
        if clickData is None:
            figure["data"][0]["marker"]["color"][2] = "grey"
            return figure, {"BC": True, "D": 1}

        point = clickData["points"][0]
        selected_idx = point["pointIndex"]
        transition = point["y"]

        for i in range(len(figure["data"][0]["marker"]["color"])):
            figure["data"][0]["marker"]["color"][i] = "blue"
        figure["data"][0]["marker"]["color"][selected_idx] = "grey"
        transition_data = {
            "BC": "T" in transition.split("=")[1],
            "D": int(transition.split("=")[2]),
        }
        return figure, transition_data

    @app.callback(
        [
            Output("feed-dropdown", "options"),
            Output("feed-dropdown", "value"),
        ],
        Input("file-data", "data"),
    )
    def update_dropdown_options(data):
        if data is None:
            return []
        options = [{"label": filename, "value": filename} for filename in data.keys()]
        value = options[0]["value"] if options else None
        return options, value

    @app.callback(
        [
            Output("date-picker-range", "start_date"),
            Output("date-picker-range", "end_date"),
            Output("date-picker-range", "min_date_allowed"),
            Output("date-picker-range", "max_date_allowed"),
        ],
        Input("feed-dropdown", "value"),
        State("file-data", "data"),
    )
    def update_date_picker(selected_file, data):
        if selected_file is None or data is None:
            return None, None, None, None

        timestamps = data[selected_file]["timestamps"]
        if not timestamps:
            return None, None, None, None

        timestamps = pd.to_datetime(timestamps)
        start_date = min(timestamps).date()
        end_date = max(timestamps).date()
        return start_date, end_date, start_date, end_date
