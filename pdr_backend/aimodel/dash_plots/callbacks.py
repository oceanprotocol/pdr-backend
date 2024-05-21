from dash import Input, Output
import pandas as pd
import os
import dash
import numpy as np
from dash import dcc, html
from scipy import stats
import plotly.express as px
from pdr_backend.aimodel.dash_plots.util import get_figures_by_state
from pdr_backend.aimodel.dash_plots.view_elements import (
    get_header_elements, display_on_column_graphs
)
from pdr_backend.aimodel.autocorrelation import AutocorrelationPlotdataFactory, AutocorrelationPlotdata, plot_autocorrelation
from pdr_backend.aimodel.autocorrelation_plotter import plot_autocorrelation_plotly


def get_callbacks(app):
    @app.callback(
        Output('data-store', 'data'),
        Input('arima-graphs', 'id')
    )
    # pylint: disable=unused-argument
    def load_data(arg):
        return []
    
    @app.callback(
        Output('arima-graphs', 'children'),
        Input('data-store', 'data')
    )
    # pylint: disable=unused-argument
    def create_charts(d):
        nlags = 5
        do_boxcox = True
        differencing_order = 1

        filebase = "binance_BTC-USDT_5m.parquet"
        log_dir = "./parquet_data" # type: ignore[attr-defined]
        file = os.path.join(log_dir, filebase)
        df = pd.read_parquet(file)  # all data start_time = UnixTimeMs(df["timestamp"][0])
        BTC_COL = "close"
        y = df[BTC_COL].array
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
        fig1 = plot_autocorrelation(data)
        #fig2 = px.line(df, x='Date', y='Value', title='Line Chart Example')
        #fig3 = px.line(df, x='Date', y='Value', title='Line Chart Example')
        #figures = []
        #figures.append(fig1, fig2, fig3)


        elements = get_header_elements()
        elements.append(display_on_column_graphs({"fig": fig1, "graph_id": "autocorelation"}))

        #elements.append(display_on_column_graphs(elements))

        return elements
