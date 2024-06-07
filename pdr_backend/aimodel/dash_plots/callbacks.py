from datetime import datetime

import dash
import numpy as np
import pandas as pd
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from scipy import stats

from pdr_backend.aimodel.autocorrelation import AutocorrelationPlotdataFactory
from pdr_backend.aimodel.autocorrelation_plotter import (
    get_transitions,
    plot_acf,
    plot_pacf,
)
from pdr_backend.aimodel.dash_plots.tooltips_text import (
    AUTOCORRELATION_TOOLTIP,
    SEASONAL_DECOMP_TOOLTIP,
    TRANSITION_TOOLTIP,
)
from pdr_backend.aimodel.dash_plots.util import (
    filter_file_data_by_date,
    read_files_from_directory,
)
from pdr_backend.aimodel.dash_plots.view_elements import get_column_graphs
from pdr_backend.aimodel.seasonal import SeasonalDecomposeFactory, SeasonalPlotdata
from pdr_backend.aimodel.seasonal_plotter import (
    create_seasonal_plot,
    plot_relative_energies,
)
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.util.time_types import UnixTimeS

DATE_STRING_FORMAT = "%Y-%m-%d"


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(Output("file-data", "data"), Input("data-folder", "data"))
    def read_from_file(data):
        files_dir = data
        data = read_files_from_directory(files_dir)
        return data

    @app.callback(
        Output("loading", "custom_spinner"), Input("autocorelation-lag", "value")
    )
    def custom_spinner(autocorelation_lag):
        lag = int(autocorelation_lag) if autocorelation_lag else 0
        return html.H2(
            [
                (
                    "This could take several seconds, please be patient "
                    if lag > 50
                    else ""
                ),
                dbc.Spinner(),
            ],
            style={"height": "100%"},
        )

    @app.callback(Output("error-message", "children"), Input("file-data", "data"))
    def display_read_data_error(store_data):
        if not store_data:
            return html.H2(
                "No data found! Fetch ohlcv data before running the ARIMA plots."
            )
        return None

    @app.callback(
        Output("autocorelation_column", "children"),
        [
            Input("feed-dropdown", "value"),
            Input("date-picker-range", "start_date"),
            Input("date-picker-range", "end_date"),
            Input("transition-data", "data"),
            Input("autocorelation-lag", "value"),
        ],
        State("file-data", "data"),
    )
    def create_autocorelation_plots(
        feed_data,
        date_picker_start_date,
        date_picker_end_date,
        transition,
        lag,
        files_data,
    ):
        if transition is None:
            return dash.no_update

        nlags = int(lag) if lag is not None else 1
        do_boxcox = transition["BC"]
        differencing_order = transition["D"]

        files_data[feed_data] = filter_file_data_by_date(
            files_data[feed_data],
            datetime.strptime(date_picker_start_date, DATE_STRING_FORMAT),
            datetime.strptime(date_picker_end_date, DATE_STRING_FORMAT),
        )

        y = files_data[feed_data]["close_data"]

        # get data for autocorelation
        y = np.array(y)
        if do_boxcox:
            y, _ = stats.boxcox(y)

        for _ in range(differencing_order):
            y = y[1:] - y[:-1]

        data = AutocorrelationPlotdataFactory.build(y, nlags)
        transition_text = f" for BC={'T' if do_boxcox else 'F'},D={differencing_order}"

        acf = plot_acf(data)
        pacf = plot_pacf(data)

        autocorelation_charts = get_column_graphs(
            [
                {"fig": acf, "graph_id": "autocorelation"},
                {"fig": pacf, "graph_id": "pautocorelation"},
            ],
            title="Autocorrelation (ACF)" + transition_text,
            tooltip=AUTOCORRELATION_TOOLTIP,
        )
        return autocorelation_charts

    @app.callback(
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
    def create_seasonal_plots(
        feed_data, date_picker_start_date, date_picker_end_date, transition, files_data
    ):
        if transition is None:
            return dash.no_update

        do_boxcox = transition["BC"]
        differencing_order = transition["D"]

        files_data[feed_data] = filter_file_data_by_date(
            files_data[feed_data],
            datetime.strptime(date_picker_start_date, DATE_STRING_FORMAT),
            datetime.strptime(date_picker_end_date, DATE_STRING_FORMAT),
        )

        # get data for seasonal
        y = files_data[feed_data]["close_data"]
        y = np.array(y)
        timestamp_str = files_data[feed_data]["timestamps"][0]
        st = UnixTimeS(timestamp_str.timestamp()).to_milliseconds()
        t = ArgTimeframe(feed_data.split("_")[-1])
        dr = SeasonalDecomposeFactory.build(t, y)

        plotdata = SeasonalPlotdata(st, dr)
        transition_text = f" for BC={'T' if do_boxcox else 'F'},D={differencing_order}"

        relativeEnergies = plot_relative_energies(plotdata)
        seasonal_plots = create_seasonal_plot(plotdata)

        seasonal_charts = get_column_graphs(
            [
                {
                    "fig": relativeEnergies,
                    "graph_id": "relativeEnergies",
                    "height": 80 / 5,
                },
                {
                    "fig": seasonal_plots,
                    "graph_id": "seasonal_plots",
                    "height": 80 - 80 / 5,
                },
            ],
            title="Seasonal Decomp." + transition_text,
            tooltip=SEASONAL_DECOMP_TOOLTIP,
        )

        return seasonal_charts

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
            datetime.strptime(date_picker_start_date, DATE_STRING_FORMAT),
            datetime.strptime(date_picker_end_date, DATE_STRING_FORMAT),
        )
        figure = get_transitions(None, files_data[feed_data]["close_data"])
        transitions = get_column_graphs(
            [{"fig": figure, "graph_id": "transition_graph"}],
            title="ADF",
            tooltip=TRANSITION_TOOLTIP,
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
            figure["data"][0]["marker"]["color"][1] = "grey"
            return figure, {"BC": True, "D": 1}

        point = clickData["points"][0]
        selected_idx = point["pointIndex"]
        transition = point["y"]

        for i in range(len(figure["data"][0]["marker"]["color"])):
            figure["data"][0]["marker"]["color"][i] = "white"
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
