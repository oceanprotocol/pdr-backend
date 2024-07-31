from dash import html, dcc
import dash_bootstrap_components as dbc

from pdr_backend.pdr_dashboard.dash_components.view_elements import get_metric
from pdr_backend.pdr_dashboard.dash_components.util import get_feeds_stats_from_db


class FeedsPage:
    def __init__(self, app):
        self.app = app
        self.lake_dir = app.lake_dir

    def layout(self):
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
                self.get_metrics_row(),
            ],
            style={"height": "100%"},
        )

    def get_metrics_row(self):
        stats = get_feeds_stats_from_db(self.lake_dir)

        return html.Div(
            [
                html.Div(
                    [
                        html.H3("Metrics"),
                        html.Div(
                            [
                                get_metric(
                                    label=key,
                                    value=value,
                                    value_id=f"feeds_page_{key}_metric",
                                )
                                for key, value in stats.items()
                            ],
                            style={"display": "flex"},
                        ),
                    ],
                    style={"width": "100%"},
                ),
            ],
            style={"display": "flex"},
        )
