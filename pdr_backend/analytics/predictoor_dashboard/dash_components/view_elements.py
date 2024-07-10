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
                ),
                id="feeds_container",
                style={"height": "50%"},
            ),
            html.Div(
                get_table(
                    table_id="predictoors_table",
                    table_name="Predictoors",
                    searchable_field="user",
                    columns=[],
                    data=None,
                ),
                id="predictoors_container",
                style={"height": "50%"},
            ),
        ],
        style={
            "height": "100%",
            "width": "20%",
            "marginTop": "8px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-around",
        },
    )


def get_graphs_column():
    return html.Div(
        [
            html.Div(id="accuracy_chart"),
            html.Div(id="profit_chart"),
            html.Div(id="stake_chart"),
        ],
        id="graphs_container",
        style={
            "height": "100%",
            "width": "80%",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-around",
            "paddingLeft": "40px",
        },
    )


def get_layout():
    return html.Div(
        [
            dcc.Store(id="data-folder"),
            dcc.Store(id="feeds-data"),
            dcc.Store(id="predictoors-data"),
            dcc.Store(id="payouts-data"),
            dcc.Store(id="predictoors-stake-data"),
            html.H1(
                "Predictoor dashboard",
                id="page_title",
                style={"width": "100%", "textAlign": "center"},
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
                    "height": "100%",
                    "width": "100%",
                },
                custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
            ),
        ],
    )


def get_main_container():
    return html.Div(
        [get_input_column(), get_graphs_column()],
        style={
            "height": "100%",
            "width": "100%",
            "display": "flex",
            "justifyContent": "space-between",
        },
    )


def get_table(table_id, table_name, searchable_field, columns, data):
    return html.Div(
        [
            html.Div(
                [
                    html.Span(table_name, style={"fontSize": "20px"}),
                    dcc.Input(
                        id=f"search-input-{table_name}",
                        type="text",
                        placeholder=f"Search for {searchable_field}",
                        debounce=True,  # Trigger the input event after user stops typing
                        style={
                            "fontSize": "15px",
                            "height": "100%",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
            ),
            dash_table.DataTable(
                id=table_id,
                columns=[{"name": col, "id": col} for col in columns],
                data=data,
                row_selectable="multi",  # Can be 'multi' for multiple rows
                selected_rows=[],
                style_cell={"textAlign": "left"},
                style_table={
                    "height": "38vh",
                    "width": "100%",
                    "overflow": "auto",
                    "marginTop": "5px",
                },
                fill_width=True,
            ),
        ],
        style={"marginBottom": "40px"},
    )


def get_graph(figure):
    return dcc.Graph(figure=figure, style={"width": "100%", "height": "30vh"})
