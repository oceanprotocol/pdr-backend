#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table


def display_plots_view(columns):
    return html.Div(
        columns,
        id="plots_container",
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "justifyContent": "space-around",
        },
    )


# pylint: disable=line-too-long
def get_column_graphs(parent_id: str, figures: list[dict], title: str, tooltip: str):
    height_percentage = 80 / (len(figures) if (title != "ADF") else 2)
    figures = [
        dcc.Graph(
            figure=fig["fig"],
            id=fig["graph_id"],
            style={
                "width": "100%",
                "height": str(fig.get("height", height_percentage)) + "vh",
                "padding": "0",
            },
        )
        for fig in figures
    ]
    return get_column_display(parent_id, figures, title, tooltip)


# pylint: disable=line-too-long
def get_column_display(parent_id: str, figures: list[dict], title: str, tooltip: str):
    return (
        html.Div(
            [
                html.Span(
                    children=title + " ⓘ",
                    id=parent_id + "-title",
                    style={
                        "textAlign": "center",
                        "fontSize": "18px",
                        "margin": "auto",
                        "cursour": "pointer",
                    },
                ),
                dbc.Tooltip(
                    dcc.Markdown(tooltip),
                    target=parent_id + "-title",
                ),
            ]
            + figures,
            style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "justifyContent": "center",
                "width": "100%",
            },
        ),
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


def display_on_column(div_id: str, width: str = "30%"):
    return html.Div(
        id=div_id,
        style={
            "display": "flex",
            "flexDirection": "column",
            "height": "100%",
            "width": width,
        },
    )


def get_input_elements():
    elements = html.Div(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        id="feed-dropdown",
                        options=[],
                        value="",
                        style={
                            "width": "300px",
                            "fontSize": "22px",
                            "marginRight": "20px",
                            "height": "100%",
                        },
                    ),
                    # Date input components
                    dcc.DatePickerRange(
                        id="date-picker-range",
                        start_date=None,
                        end_date=None,
                        min_date_allowed=None,
                        max_date_allowed=None,
                    ),
                ],
                style={
                    "height": "100%",
                    "width": "100%",
                    "display": "flex",
                    "justifyContent": "flex-start",
                    "alignItems": "center",
                    "padding": "10px",
                },
            ),
            html.Div(
                [
                    html.Label("Lag", style={"fontSize": "20px"}),
                    dcc.Input(
                        id="autocorelation-lag",
                        type="number",
                        value="10",
                        style={
                            "width": "100px",
                            "fontSize": "22px",
                            "marginLeft": "20px",
                            "height": "100%",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "flex-start",
                    "alignItems": "center",
                },
            ),
        ],
        style={
            "height": "100%",
            "margin": "auto",
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "10px",
        },
    )

    return elements


def get_graphs_container():
    return html.Div(
        [
            display_on_column("transition_column", "17.5%"),
            display_on_column("seasonal_column", "65%"),
            display_on_column("autocorelation_column", "22.5%"),
        ],
        id="arima-graphs",
        style={
            "width": "100%",
            "height": "100%",
            "display": "flex",
            "justifyContent": "space-between",
        },
    )


def get_layout():
    return html.Div(
        [
            dcc.Store(id="data-folder"),
            dcc.Store(id="file-data"),
            dcc.Store(id="window-data"),
            dcc.Store(id="transition-data"),
            html.H1(
                "ARIMA-style feed analysis",
                id="page_title",
                style={"width": "100%", "textAlign": "center"},
            ),
            html.Div(id="input-elements", children=get_input_elements()),
            html.Div(id="error-message"),
            dcc.Loading(
                id="loading",
                type="default",
                children=get_graphs_container(),
                style={"height": "100%", "display": "flex", "alignItems": "flexStart"},
                custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
            ),
        ]
    )
