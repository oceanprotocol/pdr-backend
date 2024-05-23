#!/usr/bin/env python
from dash import Dash, dcc, html

from pdr_backend.aimodel.dash_plots.view_elements import display_waiting_template
from pdr_backend.aimodel.dash_plots.callbacks import get_callbacks

app = Dash(__name__)
app.config["suppress_callback_exceptions"] = True
app.layout = html.Div(
    html.Div(
        [
            html.H1(
                "ARIMA feed data",
                id="page_title",
                # stops refreshing if final state was reached. Do not remove this class!
                className="title",
                style={"width": "100%", "textAlign": "center"},
            ),
            html.Div(id="clicked-data"),
            html.Div(id="arima-graphs"),
            dcc.Loading(
                id="loading",
                type="default",
                children=html.Div(
                    id="loading-container", children=[display_waiting_template()]
                ),
            ),
        ]
    )
)

get_callbacks(app)


def arima_dash(args):
    app.run(debug=True, port=args.port)
