#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Dict, List, Optional

import dash_bootstrap_components as dbc
import polars as pl
from dash import Dash, Input, Output, html
from polars.dataframe.frame import DataFrame

from pdr_backend.lake_info.overview import TableViewsOverview, ValidationOverview
from pdr_backend.util.time_types import UnixTimeMs


class HtmlRenderer:
    def __init__(self, lake_info, table_views_overview, validation_overview):
        self.lake_info = lake_info
        self.table_views_overview = table_views_overview
        self.validation_overview = validation_overview

    def get_side_info(self, source: Dict[str, DataFrame], table_name: str):
        result = []
        has_timestamp = False

        types = []
        for col in source[table_name].iter_columns():
            if col.name == "timestamp":
                has_timestamp = True

            types.append(html.Tr([html.Td(str(col.name)), html.Td(str(col.dtype))]))

        types_table = dbc.Table(types, bordered=True)
        result.append(
            html.Div(
                [html.Strong("Schema"), types_table],
            )
        )

        if has_timestamp:
            min_badge = fallback_badge(
                "Min timestamp:", source[table_name]["timestamp"].min()
            )
            max_badge = fallback_badge(
                "Max timestamp:", source[table_name]["timestamp"].max()
            )

            result.append(html.Div([min_badge, max_badge]))

        shape = source[table_name].shape
        nrows_badge = simple_badge("Number of rows:", shape[0])
        result.append(html.Div(nrows_badge, style={"margin-bottom": "10px"}))

        return result

    def get_main_info(
        self,
        source: Dict[str, DataFrame],
        table_name: str,
        filter_value: Optional[str] = None,
    ):
        if not filter_value:
            table_type = "Preview:"
            filtered_df = source[table_name].limit(100)
        else:
            table_type = "Results:"
            filtered_df = source[table_name].filter(pl.col("user") == filter_value)

        table = dbc.Table.from_dataframe(
            filtered_df.to_pandas(),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="small",
        )

        return html.Div([html.Strong(table_type), table])

    def html_table_info(
        self,
        source: Dict[str, DataFrame],
        filter_value: Optional[str] = None,
    ):
        if not source:
            return []

        result = []
        for table_name in source:
            side_info = self.get_side_info(source, table_name)
            main_info = self.get_main_info(source, table_name, filter_value)

            result.append(
                dbc.Tab(
                    label=table_name,
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(side_info, width=3),
                                dbc.Col(main_info, width=9),
                            ],
                        ),
                    ],
                )
            )

        return dbc.Tabs(children=result, style={"margin-top": "10px"})

    def validation_report(self):
        result = []
        for key, violations in self.validation_overview.validation_results.items():
            if not violations:
                alerts = [
                    dbc.Alert(
                        [
                            html.I(className="bi bi-check-circle-fill me-2"),
                            f"{key} - No violations found",
                        ],
                        color="success",
                        className="d-flex align-items-center",
                    )
                ]
                result += alerts

                continue

            alerts = [
                dbc.Alert(
                    [html.I(className="bi bi-x-octagon-fill me-2"), violation],
                    color="danger",
                    className="d-flex align-items-center",
                )
                for violation in violations
            ]

            result += alerts

        return [html.Div(result, style={"margin-top": "10px"})]

    def show(self):
        app = Dash(
            __name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
        )

        total_violations = any(self.validation_overview.validation_results.values())

        violations_text = (
            "No violations found"
            if total_violations == 0
            else "Please check violations!"
        )

        app.layout = html.Div(
            [
                html.H2("Lake Tables"),
                dbc.Toast(
                    [html.P(violations_text, className="mb-0")],
                    id="simple-toast",
                    header="Validation result",
                    icon="success" if total_violations == 0 else "danger",
                    dismissable=True,
                    is_open=True,
                    style={"position": "fixed", "top": 10, "right": 10, "width": 350},
                ),
                dbc.Input(
                    id="userFilter",
                    placeholder="Filter tables...",
                    value="",
                    style={"margin-top": "10px"},
                ),
                dbc.Tabs(
                    [
                        dbc.Tab(
                            label="Table Info",
                            children=self.html_table_info(
                                self.table_views_overview.table_info,
                            ),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
                            id="table_info",
                        ),
                        dbc.Tab(
                            label="View Info",
                            children=self.html_table_info(
                                self.table_views_overview.view_info,
                            ),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
                            id="view_info",
                        ),
                        dbc.Tab(
                            label="Validation report",
                            children=self.validation_report(),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
                        ),
                    ],
                    style={"margin-top": "10px"},
                ),
            ],
            className="container",
            style={"margin-top": "10px"},
        )

        get_callbacks(self, app)
        app.run_server(debug=True)


def simple_badge(text, value):
    return dbc.Button(
        [
            text,
            dbc.Badge(
                str(value),
                color="light",
                text_color="primary",
                className="ms-1",
            ),
        ],
        color="primary",
    )


def fallback_badge(text, value):
    nat_str = (
        UnixTimeMs(value).to_timestr() if isinstance(value, (int, float)) else None
    )

    return dbc.Button(
        [
            text,
            dbc.Badge(
                str(value) if value is not None else "no data",
                color="light",
                text_color="primary" if value is not None else "danger",
                className="ms-1",
            ),
            " aka ",
            dbc.Badge(
                str(nat_str),
                color="light",
                text_color="primary" if value is not None else "danger",
                className="ms-1",
            ),
        ],
        color="primary" if value else "danger",
        style={"margin-bottom": "10px"},
    )


def get_callbacks(html_renderer, app):
    @app.callback(
        Output("table_info", "children"),
        Input("userFilter", "value"),
    )
    def filter_tables(filter_value):
        return html_renderer.html_table_info(
            html_renderer.table_views_overview.table_info,
            filter_value,
        )
