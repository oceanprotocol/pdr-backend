#!/usr/bin/env python
from dash import Dash, dcc, html

from pdr_backend.sim.dash_plots.callbacks import get_callbacks
from pdr_backend.sim.dash_plots.view_elements import empty_graphs_template

app = Dash(__name__)
app.config["suppress_callback_exceptions"] = True
app.layout = html.Div(
    html.Div(
        [
            html.Div(empty_graphs_template, id="live-graphs"),
            dcc.Interval(
                id="interval-component",
                interval=3 * 1000,  # in milliseconds
                n_intervals=0,
                disabled=False,
            ),
        ]
    )
)

get_callbacks(app)


def sim_dash(args):
    app.run_id = args.run_id
    app.run(debug=True, port=args.port)
