#!/usr/bin/env python
from enforce_typing import enforce_types
from dash import Dash, dcc, html
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.aimodel.dash_plots.view_elements import (
    display_waiting_template,
    get_input_elements,
)
from pdr_backend.aimodel.dash_plots.callbacks import get_callbacks

app = Dash(__name__)
app.config["suppress_callback_exceptions"] = True
app.layout = html.Div(
    [
        dcc.Store(id="data-folder"),
        html.H1(
            "ARIMA feed data",
            id="page_title",
            # stops refreshing if final state was reached. Do not remove this class!
            className="title",
            style={"width": "100%", "textAlign": "center"},
        ),
        html.Div(id="input-elements", children=get_input_elements()),
        html.Div(id="clicked-data"),
        html.Div(id="arima-graphs"),
        dcc.Store(id="data-store"),
        dcc.Store(id="data-loading"),
        dcc.Loading(
            id="loading",
            type="default",
            children=html.Div(
                id="loading-container", children=[display_waiting_template()]
            ),
        ),
    ]
)

get_callbacks(app)


@enforce_types
def arima_dash(port, ppss: PPSS):
    folder = ppss.lake_ss.parquet_dir
    app.layout.children[0].data = folder
    app.run(debug=True, port=port)
