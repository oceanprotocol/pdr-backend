import os
from dash import Input, Output
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


def get_callbacks(app):
    @app.callback(
        Output("arima-graphs", "children"),
        Output("loading", "children"),
        [Input("page_title", "id")],
    )
    # pylint: disable=unused-argument
    def create_charts(n_intervals):
        nlags = 5
        do_boxcox = True
        differencing_order = 1

        filebase = "binance_BTC-USDT_5m.parquet"
        log_dir = "./parquet_data"  # type: ignore[attr-defined]
        file = os.path.join(log_dir, filebase)

        # get data from file
        df = pd.read_parquet(file)
        BTC_COL = "close"
        y = df[BTC_COL].array

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
        print(data.acf_results)

        # get data for seasonal
        y = df[BTC_COL].array
        st = UnixTimeMs(df["timestamp"][0])
        t = ArgTimeframe("5m")
        dr = SeasonalDecomposeFactory.build(t, y)

        plotdata = SeasonalPlotdata(st, dr)

        acf = plot_acf(data)
        pacf = plot_pacf(data)

        fig1 = plot_relative_energies(plotdata)
        fig2 = plot_observed(plotdata)
        fig3 = plot_trend(plotdata)
        fig4 = plot_seasonal(plotdata)
        fig5 = plot_residual(plotdata)

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
                    {"fig": fig1, "graph_id": "relativeEnergies"},
                    {"fig": fig2, "graph_id": "observed"},
                    {"fig": fig3, "graph_id": "trend"},
                    {"fig": fig4, "graph_id": "seasonal"},
                    {"fig": fig5, "graph_id": "ressidual"},
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

        return display_plots_view(columns), None

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
