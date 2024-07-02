import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table


def get_input_column():
    return html.Div(
        [html.Div(id="feeds_container"), html.Div(id="predictoors_container")]
    )


def get_graphs_column():
    return html.Div(id="graphs_container")


def get_layout():
    return html.Div(
        [
            dcc.Store(id="data-folder"),
            dcc.Store(id="feeds-data"),
            html.H1(
                "Predictoor dashboard",
                id="page_title",
                style={"width": "100%", "textAlign": "center"},
            ),
            html.Div(id="error-message"),
            dcc.Loading(
                id="loading",
                type="default",
                children=[get_input_column(), get_input_column()],
                style={"height": "100%", "display": "flex", "alignItems": "flexStart"},
                custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
            ),
        ]
    )


def get_table(columns, data):
    return dash_table.DataTable(
        id="transition_table",
        columns=[{"name": col, "id": col} for col in columns],
        data=data,
        row_selectable="single",  # Can be 'multi' for multiple rows
        selected_rows=[2],
        style_cell={"textAlign": "left"},
        style_table={
            "marginTop": "20px",
            "paddingRight": "20px",
        },
        fill_width=True,
    )
