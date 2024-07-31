from dash import html, dcc
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_feeds_data_for_feeds_table,
    get_feeds_table_area,
)
from pdr_backend.pdr_dashboard.dash_components.util import (
    get_feed_payouts_stats_from_db,
)

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

def get_main_container(app):
    feed_stats = get_feed_payouts_stats_from_db(app.lake_dir)

    feed_cols, feed_data = get_feeds_data_for_feeds_table(app, feed_stats)

    return html.Div(
        [get_feeds_table_area(feed_cols, feed_data)],
        className="main-container",
    )
