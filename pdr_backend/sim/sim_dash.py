#!/usr/bin/env python
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html
from pdr_backend.sim.dash_plots.callbacks import get_callbacks
from pdr_backend.sim.dash_plots.view_elements import get_main_container

bootstrap_css_url = dbc.themes.BOOTSTRAP
google_fonts_url = (
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
)

app = Dash(__name__, external_stylesheets=[bootstrap_css_url, google_fonts_url])
app.config["suppress_callback_exceptions"] = True
app.layout = html.Div(
    [
        get_main_container(),
        dcc.Interval(
            id="interval-component",
            interval=3 * 1000,  # in milliseconds
            n_intervals=0,
            disabled=False,
        ),
    ],
    style={"height": "100vh"},
)

get_callbacks(app)


def sim_dash(args):
    app.run_id = args.run_id
    app.run(debug=True, port=args.port)
