from dash import html, dcc
import dash_bootstrap_components as dbc


def layout():
    return html.Div(
        [
            dcc.Store(id="user-payout-stats"),
            html.H1(
                "Feeds page content",
                id="page_title_feeds",
            ),
            dcc.Loading(
                id="loading",
                type="default",
                children=[],
                custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
            ),
        ],
        style={"height": "100%"},
    )
