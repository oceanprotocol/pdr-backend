#!/usr/bin/env python
#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import webbrowser
import dash_bootstrap_components as dbc
from dash import Dash
from pdr_backend.sim.dash_plots.callbacks import get_callbacks
from pdr_backend.sim.dash_plots.view_elements import get_layout

bootstrap_css_url = dbc.themes.BOOTSTRAP
google_fonts_url = (
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
)

app = Dash(__name__, external_stylesheets=[bootstrap_css_url, google_fonts_url])
app.config["suppress_callback_exceptions"] = True
app.layout = get_layout()
get_callbacks(app)


def sim_dash(args):
    app.run_id = args.run_id
    if not args.debug_mode:
        webbrowser.open(f"http://127.0.0.1:{args.port}/")
    app.run(debug=args.debug_mode, port=args.port)
