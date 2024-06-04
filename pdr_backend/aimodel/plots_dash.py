#!/usr/bin/env python
import webbrowser

import dash_bootstrap_components as dbc
from dash import Dash, dcc, html
from enforce_typing import enforce_types

from pdr_backend.aimodel.dash_plots.callbacks import get_callbacks
from pdr_backend.aimodel.dash_plots.view_elements import (
    get_graphs_container,
    get_input_elements,
)
from pdr_backend.ppss.ppss import PPSS

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config["suppress_callback_exceptions"] = True
app.layout = html.Div(
    [
        dcc.Store(id="data-folder"),
        dcc.Store(id="file-data"),
        dcc.Store(id="window-data"),
        dcc.Store(id="transition-data"),
        html.H1(
            "ARIMA-style feed analysis",
            id="page_title",
            style={"width": "100%", "textAlign": "center"},
        ),
        html.Div(id="input-elements", children=get_input_elements()),
        html.Div(id="error-message"),
        dcc.Loading(
            id="loading",
            type="default",
            children=get_graphs_container(),
            style={"height": "100%", "display": "flex", "alignItems": "flexStart"},
            custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
        ),
    ]
)

get_callbacks(app)


@enforce_types
def arima_dash(ppss: PPSS):
    port = 8050
    webbrowser.open(f"http://127.0.0.1:{port}/")
    folder = ppss.lake_ss.parquet_dir
    app.layout.children[0].data = folder
    app.run(debug=True, port=port)
