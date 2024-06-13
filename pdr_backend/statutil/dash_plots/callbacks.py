from datetime import datetime

import dash
import numpy as np
import pandas as pd
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

from pdr_backend.statutil.autocorrelation_plotdata import (
    AutocorrelationPlotdataFactory,
)
from pdr_backend.statutil.autocorrelation_plotter import (
    get_transitions,
    plot_acf,
    plot_pacf,
    TRANSITION_OPTIONS,
)
from pdr_backend.statutil.dash_plots.tooltips_text import (
    AUTOCORRELATION_TOOLTIP,
    SEASONAL_DECOMP_TOOLTIP,
    TRANSITION_TOOLTIP,
)
from pdr_backend.statutil.dash_plots.util import (
    filter_file_data_by_date,
    read_files_from_directory,
)
from pdr_backend.statutil.dash_plots.view_elements import (
    get_column_graphs,
    get_column_display,
)
from pdr_backend.statutil.seasonal import SeasonalDecomposeFactory, SeasonalPlotdata
from pdr_backend.statutil.seasonal_plotter import (
    create_seasonal_plot,
    plot_relative_energies,
)
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.statutil.boxcox import safe_boxcox
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
            y = safe_boxcox(y)

        for _ in range(differencing_order):
            y = y[1:] - y[:-1]

        data = AutocorrelationPlotdataFactory.build(y, nlags)
        transition_text = f" for BC={'T' if do_boxcox else 'F'},D={differencing_order}"

        acf = plot_acf(data)
        pacf = plot_pacf(data)

        autocorelation_charts = get_column_graphs(
            parent_id="Autocorelation",
            figures=[
                {"fig": acf, "graph_id": "autocorelation"},
                {"fig": pacf, "graph_id": "pautocorelation"},
            ],
            title="ACF & PACF" + transition_text,
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
        st = UnixTimeS(int(timestamp_str.timestamp())).to_milliseconds()
        t = ArgTimeframe(feed_data.split("_")[-1])
        dr = SeasonalDecomposeFactory.build(t, y)

        plotdata = SeasonalPlotdata(st, dr)
        transition_text = f" for BC={'T' if do_boxcox else 'F'},D={differencing_order}"

        relativeEnergies = plot_relative_energies(plotdata)
        seasonal_plots = create_seasonal_plot(plotdata)

        seasonal_charts = get_column_graphs(
            parent_id="Seasonal",
            figures=[
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
        if not files_data:
            return dash.no_update

        files_data[feed_data] = filter_file_data_by_date(
            files_data[feed_data],
            datetime.strptime(date_picker_start_date, DATE_STRING_FORMAT),
            datetime.strptime(date_picker_end_date, DATE_STRING_FORMAT),
        )
        table = get_transitions(None, files_data[feed_data]["close_data"])
        transition = get_column_display(
            parent_id="Transition",
            figures=[table],
            title="ADF",
            tooltip=TRANSITION_TOOLTIP,
        )

        return transition

    @app.callback(
        Output("transition-data", "data"),
        [Input("transition_table", "selected_rows")],
    )
    def update_transition_data(selectedRows):
        if len(selectedRows) <= 0:
            return {"BC": True, "D": 1}

        selectedRow = selectedRows[0]

        transition = TRANSITION_OPTIONS[selectedRow]
        transition_data = {
            "BC": "T" in transition.split("=")[1],
            "D": int(transition.split("=")[2]),
        }
        return transition_data

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
