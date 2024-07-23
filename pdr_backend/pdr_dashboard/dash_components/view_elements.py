import copy
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html
from pdr_backend.pdr_dashboard.dash_components.util import (
    get_feed_ids_based_on_predictoors_from_db,
)


def get_feeds_data(app):
    data = copy.deepcopy(app.feeds_data)

    for feed in data:
        del feed["contract"]

    columns = [{"name": col, "id": col} for col in data[0].keys()]

    return columns, data


def get_predictoors_data(app):
    columns = [{"name": col, "id": col} for col in app.predictoors_data[0].keys()]

    if app.favourite_addresses:
        data = [
            p for p in app.predictoors_data if p["user"] in app.favourite_addresses
        ] + [
            p for p in app.predictoors_data if p["user"] not in app.favourite_addresses
        ]
    else:
        data = app.predictoors_data

    return columns, data


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
                    "height": "50%",
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


def get_graphs_column_metrics_row():
    return html.Div(
        [
            get_metric(label="Avg Accuracy", value="50%", value_id="accuracy_metric"),
            get_metric(label="Total Profit", value="50%", value_id="profit_metric"),
            get_metric(label="Avg Stake", value="50%", value_id="stake_metric"),
            get_date_period_selection_component(),
        ],
        id="metrics_container",
        style={
            "height": "12%",
            "display": "flex",
            "justifyContent": "space-between",
        },
    )


def get_date_period_selection_component():
    return html.Div(
        [
            dcc.RadioItems(
                id="date-period-radio-items",
                options=[
                    {"label": "1D", "value": "1"},
                    {"label": "1W", "value": "7"},
                    {"label": "1M", "value": "30"},
                    {"label": "ALL", "value": "0"},
                ],
                value="0",  # default selected value
                labelStyle={"display": "inline-block", "margin-right": "10px"},
            ),
            html.Span("there is no data available", id="available_data_period_text"),
        ]
    )


def get_graphs_column_plots_row():
    return html.Div(
        [
            html.Div(id="accuracy_chart"),
            html.Div(id="profit_chart"),
            html.Div(id="stake_chart"),
        ],
        id="plots_container",
        style={
            "height": "88%",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )


def get_metric(label, value, value_id):
    return html.Div(
        [
            html.Span(
                label,
            ),
            html.Span(value, id=value_id, style={"fontWeight": "bold"}),
        ],
        style={"display": "flex", "flexDirection": "column", "font-size": "20px"},
    )


def get_layout(app):
    return html.Div(
        [
            dcc.Store(id="user-payout-stats"),
            html.H1(
                "Predictoor dashboard",
                id="page_title",
            ),
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


def get_table(
    table_id,
    table_name,
    searchable_field,
    columns,
    data,
    selected_items=None,
    length=0,
):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                table_name, style={"fontSize": "20px", "hight": "100%"}
                            ),
                            html.Span(
                                id=f"table-rows-count-{table_id}",
                                children=f"({length})",
                                style={
                                    "fontSize": "16px",
                                    "color": "gray",
                                    "hight": "100%",
                                    "marginLeft": "4px",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justifyContet": "center",
                            "alignItems": "center",
                        },
                    ),
                    (
                        dbc.Switch(
                            id="toggle-switch-predictoor-feeds",
                            label="Predictoor feeds only",
                            value=True,
                        )
                        if table_name == "Feeds"
                        else dbc.Switch(
                            id="show-favourite-addresses",
                            label="Select configured predictoors",
                            value=bool(selected_items),
                        )
                    ),
                ],
                className="table-title",
            ),
            html.Div(
                [
                    dcc.Input(
                        id=f"search-input-{table_name}",
                        type="text",
                        placeholder=f"Search for {searchable_field}",
                        debounce=True,  # Trigger the input event after user stops typing
                        style={"fontSize": "15px", "min-width": "100px"},
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Select All",
                                id=f"select-all-{table_id}",
                                n_clicks=0,
                                className="button-select-all",
                            ),
                            html.Button(
                                "Clear",
                                id=f"clear-all-{table_id}",
                                n_clicks=0,
                                className="button-clear-all",
                            ),
                        ],
                        className="wrap-with-gap",
                    ),
                ],
                className="wrap-with-gap",
            ),
            dash_table.DataTable(
                id=table_id,
                columns=columns,
                data=data,
                row_selectable="multi",  # Can be 'multi' for multiple rows
                selected_rows=selected_items if selected_items else [],
                sort_action="native",  # Enables data to be sorted
                style_cell={"textAlign": "left"},
                style_table={
                    "height": "30vh",
                    "width": "100%",
                    "overflow": "auto",
                    "paddingTop": "5px",
                },
                fill_width=True,
            ),
        ],
    )


def get_graph(figure):
    return dcc.Graph(figure=figure, style={"width": "100%", "height": "25vh"})
