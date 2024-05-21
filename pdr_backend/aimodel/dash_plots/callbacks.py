from dash import Input, Output
import pandas as pd
import os
import dash
from dash import dcc, html
from scipy import stats
import plotly.express as px
from pdr_backend.aimodel.dash_plots.util import get_figures_by_state
from pdr_backend.aimodel.dash_plots.view_elements import (
    get_header_elements,
)
from pdr_backend.aimodel.autocorrelation import AutocorrelationPlotdataFactory


def get_callbacks(app):
    @app.callback(
        Output('data-store', 'data'),
        Input('arima-graphs', 'id')
    )
    # pylint: disable=unused-argument
    def load_data(arg):
        nlags = 5
        do_boxcox = True
        differencing_order = 1

        filebase = "binance_BTC-USDT_5m.parquet"
        log_dir = "./parquet_data" # type: ignore[attr-defined]
        file = os.path.join(log_dir, filebase)
        df = pd.read_parquet(file)  # all data start_time = UnixTimeMs(df["timestamp"][0])
        BTC_COL = "close"
        y = df[BTC_COL].array
        if do_boxcox:
            y, _ = stats.boxcox(y)
        for _ in range(differencing_order):
            y = y[1:] - y[:-1]

        data = AutocorrelationPlotdataFactory.build(y, nlags)
        data =["1", "2"]

        return data
    
    @app.callback(
        Output('arima-graphs', 'children'),
        Input('data-store', 'data')
    )
    # pylint: disable=unused-argument
    def create_charts(data):
        if data is None:
            return dash.no_update
        #Convert data back to DataFrame
        df = pd.DataFrame(data.acf_results)
        # Create a line chart
        fig = px.line(df, x='Date', y='Value', title='Line Chart Example')

        elements = get_header_elements()

        elements.append(html.Div(
            [
                dcc.Graph(figure=fig, id="name1", style={"width": "100%"}),
            ],
            style={"display": "flex", "justifyContent": "space-between"},
        ))

        return get_header_elements()
