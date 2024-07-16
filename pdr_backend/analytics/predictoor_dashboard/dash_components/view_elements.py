import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table


def get_input_column():
    return html.Div(
        [
            html.Div(
                get_table(
                    table_id="feeds_table",
                    table_name="Feeds",
                    searchable_field="pair",
                    columns=[],
                    data=None,
                    default_sorting=[],
                ),
                id="feeds_container",
            ),
            html.Div(
                get_table(
                    table_id="predictoors_table",
                    table_name="Predictoors",
                    searchable_field="user",
                    columns=[],
                    data=None,
                    default_sorting=[
                        {"column_id": "total_profit", "direction": "desc"}
                    ],
                ),
                id="predictoors_container",
            ),
        ],
        style={
            "height": "100%",
            "width": "20%",
            "paddingTop": "8px",
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
            "width": "80%",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "start",
            "paddingLeft": "40px",
        },
    )


def get_graphs_column_metrics_row():
    return html.Div(
        [
            get_metric(label="Avg Accuracy", value="50%", value_id="accuracy_metric"),
            get_metric(label="Total Profit", value="50%", value_id="profit_metric"),
            get_metric(label="Avg Stake", value="50%", value_id="stake_metric"),
        ],
        id="metrics_container",
        style={
            "height": "12%",
            "display": "flex",
            "justifyContent": "space-between",
        },
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


def get_layout():
    return html.Div(
        [
            dcc.Store(id="data-folder"),
            dcc.Store(id="feeds-data"),
            dcc.Store(id="predictoors-data"),
            dcc.Store(id="user-payout-stats"),
            html.H1(
                "Predictoor dashboard",
                id="page_title",
                style={
                    "width": "100%",
                    "textAlign": "center",
                    "paddingTop": "10px",
                    "paddingBottom": "20px",
                },
            ),
            html.Div(
                id="error-message",
                style={
                    "display": "flex",
                    "width": "100%",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "textAlign": "center",
                },
            ),
            dcc.Loading(
                id="loading",
                type="default",
                children=get_main_container(),
                style={
                    "height": "calc( 100vh - 105px )",
                    "width": "100%",
                },
                custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
            ),
        ],
        style={"height": "100%"},
    )


def get_main_container():
    return html.Div(
        [get_input_column(), get_graphs_column()],
        style={
            "height": "calc( 100vh - 105px )",
            "width": "100%",
            "display": "flex",
            "justifyContent": "space-between",
        },
    )


def get_table(table_id, table_name, searchable_field, columns, data, default_sorting):
    return html.Div(
        [
            html.Div(
                [
                    html.Span(table_name, style={"fontSize": "20px"}),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
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
                                style={
                                    "border": "0",
                                    "min-width": "90px",
                                    "fontSize": "15px",
                                    "backgroundColor": "#dedede",
                                    "borderRadius": "3px",
                                },
                            ),
                            html.Button(
                                "Clear",
                                id=f"clear-all-{table_id}",
                                n_clicks=0,
                                style={
                                    "border": "0",
                                    "fontSize": "15px",
                                    "backgroundColor": "#dedede",
                                    "borderRadius": "3px",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "gap": "10px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "gap": "10px",
                },
            ),
            dash_table.DataTable(
                id=table_id,
                columns=[{"name": col, "id": col, "sortable": True} for col in columns],
                sort_by=default_sorting,
                data=data,
                row_selectable="multi",  # Can be 'multi' for multiple rows
                selected_rows=[],
                sort_action="native",  # Enables data to be sorted
                style_cell={"textAlign": "left"},
                style_table={
                    "height": "34vh",
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
