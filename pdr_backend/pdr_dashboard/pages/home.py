from dash import html, dcc
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.dash_components.view_elements import get_main_container


def layout(app):
    return html.Div(
        [
            dcc.Store(id="user-payout-stats"),
            dcc.Loading(
                id="loading",
                type="default",
                children=get_main_container(app),
                custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
            ),
        ],
        style={"height": "100%"},
    )
