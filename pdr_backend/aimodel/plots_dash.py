#!/usr/bin/env python
from dash import Dash, dcc, html

from pdr_backend.aimodel.dash_plots.callbacks import get_callbacks
from pdr_backend.aimodel.dash_plots.view_elements import empty_graphs_template

app = Dash(__name__)
app.config["suppress_callback_exceptions"] = True
app.layout = html.Div(
    html.Div(
        [
            html.Div(empty_graphs_template, id="arima-graphs"),
        ]
    )
)

get_callbacks(app)


def arima_dash(args):
    app.run(debug=True, port=args.port)
