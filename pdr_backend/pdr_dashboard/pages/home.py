import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_date_period_selection_component,
    get_metric,
    get_tooltip_and_button,
)


class HomePage:
    def __init__(self, app):
        self.app = app

        self.selected_predictoors = []
        self.selected_feeds = []

    def layout(self):
        return html.Div(
            self.get_main_container(),
            className="page-layout",
        )

    def get_main_container(self):
        return html.Div(
            [self.get_input_column(), self.get_graphs_column()],
            className="main-container",
        )

    def get_graphs_column(self):
        return html.Div(
            [
                self.get_graphs_column_metrics_row(),
                dcc.Loading(
                    id="loading",
                    type="default",
                    children=self.get_graphs_column_plots_row(),
                    custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
                ),
            ],
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

    def get_feeds_for_favourite_predictoors(self, feed_data):
        feed_ids = self.app.db_getter.feed_ids_based_on_predictoors()

        if not feed_ids:
            return [], feed_data

        feed_data = [
            feed
            for feed in self.app.db_getter.feeds_data
            if feed["contract"] in feed_ids
        ]

        return list(range(len(feed_ids))), feed_data

    def get_input_column(self):
        feed_cols, feed_data = self.app.db_getter.homepage_feeds_cols
        predictoor_cols, predictoor_data = self.app.db_getter.homepage_predictoors_cols

        self.selected_predictoors = list(
            range(len(self.app.db_getter.favourite_addresses))
        )
        self.selected_feeds, feed_data = self.get_feeds_for_favourite_predictoors(
            feed_data
        )

        return html.Div(
            [
                html.Div(
                    self.get_table(
                        table_id="predictoors_table",
                        columns=predictoor_cols,
                        data=predictoor_data,
                    ),
                    id="predictoors_container",
                ),
                html.Div(
                    self.get_table(
                        table_id="feeds_table",
                        columns=feed_cols,
                        data=feed_data,
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

    def get_graphs_column_plots_row(self):
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

    def get_graphs_column_metrics_row(self):
        return html.Div(
            [
                get_metric(label="Avg Accuracy", value=0.0, value_id="accuracy_metric"),
                get_metric(label="Pred Profit", value=0, value_id="profit_metric"),
                get_metric(label="Tx Costs", value=0.0, value_id="costs_metric"),
                get_metric(label="Avg Stake", value=0, value_id="stake_metric"),
                get_date_period_selection_component(),
            ],
            id="metrics_container",
            style={
                "height": "12%",
                "display": "flex",
                "justifyContent": "space-between",
            },
        )

    def get_feeds_switch(self):
        return html.Div(
            [
                dbc.Switch(
                    id="toggle-switch-predictoor-feeds",
                    label="Predictoor feeds only",
                    value=True,
                ),
                get_tooltip_and_button("switch-feeds"),
            ],
            style={"display": "flex"},
        )

    def get_predictoors_switch(self):
        return html.Div(
            [
                dbc.Switch(
                    id="show-favourite-addresses",
                    label="Select configured predictoors",
                    value=bool(self.selected_predictoors),
                ),
                get_tooltip_and_button("switch-predictoors"),
            ],
            style={"display": "flex"},
        )

    def get_table(self, table_id, columns, data):
        if table_id == "predictoors_table":
            table_name = "Predictoors"
            searchable_field = "user"
            length = len(self.app.db_getter.predictoors_data)

            toggle_switch = self.get_predictoors_switch()
            selected_rows = self.selected_predictoors
        else:
            table_name = "Feeds"
            searchable_field = "pair"
            length = len(self.app.db_getter.feeds_data)

            toggle_switch = self.get_feeds_switch()
            selected_rows = self.selected_feeds

        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    table_name,
                                    style={"fontSize": "20px", "height": "100%"},
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
                        toggle_switch,
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
                    columns=columns[0],
                    hidden_columns=columns[1],
                    data=data,
                    row_selectable="multi",  # Can be 'multi' for multiple rows
                    selected_rows=selected_rows,
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
