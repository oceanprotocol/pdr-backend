#!/usr/bin/env python
import webbrowser

import dash_bootstrap_components as dbc
from dash import Dash
from enforce_typing import enforce_types

from pdr_backend.statutil.dash_plots.callbacks import get_callbacks
from pdr_backend.statutil.dash_plots.view_elements import get_layout
from pdr_backend.ppss.ppss import PPSS

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config["suppress_callback_exceptions"] = True
app.layout = get_layout()
get_callbacks(app)


@enforce_types
def arima_dash(ppss: PPSS, debug_mode: bool):
    port = 8050
    if not debug_mode:
        webbrowser.open(f"http://127.0.0.1:{port}/")
    folder = ppss.lake_ss.lake_dir
    app.layout.children[0].data = folder
    app.run(debug=debug_mode, port=port)
