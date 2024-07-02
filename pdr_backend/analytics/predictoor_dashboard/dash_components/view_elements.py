import dash_bootstrap_components as dbc
from dash import dcc, html


def get_layout():
    return html.Div(
        [
            dcc.Store(id="data-folder"),
            dcc.Store(id="file-data"),
            html.H1(
                "Predictoor dashboard",
                id="page_title",
                style={"width": "100%", "textAlign": "center"},
            ),
            html.Div(id="input-elements", children=[]),
            html.Div(id="error-message"),
            dcc.Loading(
                id="loading",
                type="default",
                children=[],
                style={"height": "100%", "display": "flex", "alignItems": "flexStart"},
                custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
            ),
        ]
    )
