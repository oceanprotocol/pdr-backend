from dash import html, dcc
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_table,
    get_feeds_data,
    get_predictoors_data,
    get_metric,
    get_date_period_selection_component,
)
from pdr_backend.pdr_dashboard.dash_components.util import (
    get_feed_ids_based_on_predictoors_from_db,
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
    return html.Div(
        [get_input_column(app), get_graphs_column()],
        className="main-container",
    )


def get_graphs_column():
    return html.Div(
        [get_graphs_column_metrics_row(), get_graphs_column_plots_row()],
        id="graphs_container",
        style={
            "height": "100%",
            "width": "70%",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "start",
            "paddingLeft": "50px",
        },
    )


def get_input_column(app):
    feed_cols, feed_data = get_feeds_data(app)
    predictoor_cols, predictoor_data = get_predictoors_data(app)

    selected_predictoors = list(range(len(app.favourite_addresses)))

    if app.favourite_addresses:
        feed_ids = get_feed_ids_based_on_predictoors_from_db(
            app.lake_dir,
            app.favourite_addresses,
        )

        if feed_ids:
            feed_data = [
                feed for feed in app.feeds_data if feed["contract"] in feed_ids
            ]

        selected_feeds = list(range(len(feed_ids)))
    else:
        selected_feeds = []

    return html.Div(
        [
            html.Div(
                get_table(
                    table_id="predictoors_table",
                    table_name="Predictoors",
                    searchable_field="user",
                    columns=predictoor_cols,
                    selected_items=selected_predictoors,
                    data=predictoor_data,
                    length=len(app.predictoors_data),
                ),
                id="predictoors_container",
            ),
            html.Div(
                get_table(
                    table_id="feeds_table",
                    table_name="Feeds",
                    searchable_field="pair",
                    columns=feed_cols,
                    data=feed_data,
                    selected_items=selected_feeds,
                    length=len(app.feeds_data),
                ),
                id="feeds_container",
                style={
                    "marginTop": "20px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-end",
                },
            ),
        ],
        style={
            "height": "100%",
            "width": "30%",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )


def get_graphs_column_plots_row():
    return html.Div(
        [
            html.Div(id="accuracy_chart"),
            html.Div(id="profit_chart"),
            html.Div(
                [
                    html.Div(id="cost_chart", style={"width": "48%"}),
                    html.Div(id="stake_chart", style={"width": "48%"}),
                ],
                style={
                    "width": "100%",
                    "display": "flex",
                    "justifyContent": "space-between",
                },
            ),
        ],
        id="plots_container",
        style={
            "height": "88%",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )


def get_graphs_column_metrics_row():
    return html.Div(
        [
            get_metric(label="Avg Accuracy", value="0%", value_id="accuracy_metric"),
            get_metric(label="Pred Profit", value="0 OCEAN", value_id="profit_metric"),
            get_metric(label="Tx Costs", value="0 OCEAN", value_id="costs_metric"),
            get_metric(label="Avg Stake", value="0 OCEAN", value_id="stake_metric"),
            get_date_period_selection_component(),
        ],
        id="metrics_container",
        style={
            "height": "12%",
            "display": "flex",
            "justifyContent": "space-between",
        },
    )
