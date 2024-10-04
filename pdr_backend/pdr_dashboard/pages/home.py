import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_metric,
    get_tooltip_and_button,
    table_initial_spinner,
)

from pdr_backend.pdr_dashboard.util.format import (
    PREDICTOORS_HOME_PAGE_TABLE_COLS,
    FEEDS_HOME_PAGE_TABLE_COLS,
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
                self.get_graphs_column_plots_row(),
            ],
            id="graphs_container",
            style={
                "height": "100%",
                "width": "65%",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "start",
                "paddingLeft": "80px",
            },
        )

    def get_input_column(self):
        return html.Div(
            [
                dcc.Store(id="is-initial-table-loaded", data=False),
                dcc.Store(id="is-home-ready-to-fetch", data=None),
                html.Div(
                    self.get_table(
                        table_id="predictoors_table",
                        columns=(PREDICTOORS_HOME_PAGE_TABLE_COLS, ["full_addr"]),
                        data=[],
                    ),
                    id="predictoors_container",
                ),
                html.Div(
                    self.get_table(
                        table_id="feeds_table",
                        columns=(FEEDS_HOME_PAGE_TABLE_COLS, ["contract"]),
                        data=[],
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
                "width": "35%",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "space-between",
            },
        )

    def get_graphs_column_plots_row(self):
        return html.Div(
            [
                html.Div(
                    id="accuracy_chart",
                    children=table_initial_spinner(),
                    style={"height": "25vh"},
                ),
                html.Div(
                    id="profit_chart",
                    children=table_initial_spinner(),
                    style={"height": "25vh"},
                ),
                html.Div(
                    [
                        html.Div(
                            style={"position": "relative", "width": "48%"},
                            id="cost_chart",
                            children=table_initial_spinner(),
                        ),
                        html.Div(
                            style={"position": "relative", "width": "48%"},
                            id="stake_chart",
                            children=table_initial_spinner(),
                        ),
                    ],
                    style={
                        "width": "100%",
                        "display": "flex",
                        "justifyContent": "space-between",
                        "height": "25vh",
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
                get_metric(label="Avg Accuracy", value_id="accuracy_metric"),
                get_metric(label="Pred Profit", value_id="profit_metric"),
                get_metric(label="Tx Costs", value_id="costs_metric"),
                get_metric(label="Avg Stake", value_id="stake_metric"),
                self.get_available_data_component(),
            ],
            id="metrics_container",
            style={
                "height": "12%",
                "display": "flex",
                "justifyContent": "space-between",
            },
        )

    def get_available_data_component(self):
        return html.Div(
            [
                html.Span(
                    "selected predictoors data range",
                    style={
                        "lineHeight": "1",
                        "marginTop": "5px",
                        "marginBottom": "12px",
                    },
                ),
                html.Span(
                    "there is no data available",
                    id="available_data_period_text",
                    style={"fontWeight": "bold", "fontSize": "20px", "lineHeight": "1"},
                ),
            ],
            style={"display": "flex", "flexDirection": "column"},
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

            toggle_switch = self.get_predictoors_switch()
        else:
            table_name = "Feeds"
            searchable_field = "pair"

            toggle_switch = self.get_feeds_switch()

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
                                    children="(0)",
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
                    selected_rows=[],
                    sort_action="native",  # Enables data to be sorted
                    style_cell={"textAlign": "left"},
                    style_table={
                        "height": "30vh",
                        "width": "100%",
                        "overflow": "auto",
                        "marginTop": "5px",
                    },
                    fill_width=True,
                ),
                html.Div(
                    id=f"home_page_table_control_{table_id}",
                    children=[
                        table_initial_spinner(),
                    ],
                ),
            ],
        )
