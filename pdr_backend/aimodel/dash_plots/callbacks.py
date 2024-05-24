import datetime
from dash import Input, Output, State
import pandas as pd
from scipy import stats
import dash
import numpy as np
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.aimodel.dash_plots.view_elements import (
    display_on_column_graphs,
    display_plots_view,
)
from pdr_backend.aimodel.autocorrelation import (
    AutocorrelationPlotdataFactory,
    AutocorrelationPlotdata,
)
from pdr_backend.aimodel.autocorrelation_plotter import plot_acf, plot_pacf
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
    get_transitions,
)
from pdr_backend.aimodel.dash_plots.util import read_files_from_directory


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(Output("data-store", "data"), Input("data-folder", "data"))
    def read_from_file(data):
        print(data)
        files_dir = data
        data = read_files_from_directory(files_dir)
        return data

    @app.callback(
        Output("arima-graphs", "children"),
        [
            Input("feed-dropdown", "value"),
            Input("date-picker-range", "start_date"),
            Input("date-picker-range", "end_date"),
        ],
        State("data-store", "data"),
    )
    # pylint: disable=unused-argument
    def create_charts(
        feed_data, date_picker_start_date, date_picker_end_date, store_data
    ):
        nlags = 5
        do_boxcox = True
        differencing_order = 1

        y = store_data[feed_data]["close_data"]

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
        y = store_data[feed_data]["close_data"]
        y = np.array(y)
        timestamp_str = store_data[feed_data]["timestamps"][0]
        st = UnixTimeMs(
            datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S").timestamp()
            * 1000
        )
        t = ArgTimeframe("5m")
        dr = SeasonalDecomposeFactory.build(t, y)

        plotdata = SeasonalPlotdata(st, dr)

        acf = plot_acf(data)
        pacf = plot_pacf(data)

        relativeEnergies = plot_relative_energies(plotdata)
        observed = plot_observed(plotdata)
        trend = plot_trend(plotdata)
        seasonal = plot_seasonal(plotdata)
        ressidual = plot_residual(plotdata)

        transitions = get_transitions()

        columns = []
        columns.append(
            display_on_column_graphs(
                [
                    {"fig": transitions, "graph_id": "transition"},
                ]
            )
        )
        columns.append(
            display_on_column_graphs(
                [
                    {"fig": relativeEnergies, "graph_id": "relativeEnergies"},
                    {"fig": observed, "graph_id": "observed"},
                    {"fig": trend, "graph_id": "trend"},
                    {"fig": seasonal, "graph_id": "seasonal"},
                    {"fig": ressidual, "graph_id": "ressidual"},
                ]
            )
        )
        columns.append(
            display_on_column_graphs(
                [
                    {"fig": acf, "graph_id": "autocorelation"},
                    {"fig": pacf, "graph_id": "pautocorelation"},
                ]
            )
        )

        # elements.append(display_on_column_graphs(elements))

        return display_plots_view(columns)

    @app.callback(
        Output("transition", "figure"),
        Output("clicked-data", "children"),
        [Input("transition", "clickData")],
    )
    def display_click_data(clickData):
        if clickData is None:
            return get_transitions(), "Click on a bar to see the data"

        point = clickData["points"][0]
        selected_idx = point["pointIndex"]
        transition = point["y"]
        value = point["x"]

        fig = get_transitions(selected_idx)
        message = f"You clicked on transition '{transition}' with value {value}"
        return fig, message

    @app.callback(
        [
            Output("feed-dropdown", "options"),
            Output("feed-dropdown", "value"),
        ],
        Input("data-store", "data"),
    )
    def update_dropdown_options(data):
        if data is None:
            return []
        options = [{"label": filename, "value": filename} for filename in data.keys()]
        value = options[0]["value"] if options else None
        return options, value

    @app.callback(
        [
            Output("start-date-picker", "options"),
            Output("end-date-picker", "value"),
        ],
        Input("data-store", "data"),
    )
    def update_date_picker_value_and_range(data):
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
        State("data-store", "data"),
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
