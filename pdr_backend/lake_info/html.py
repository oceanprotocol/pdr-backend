#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Optional, Tuple

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, callback_context, dcc, html
from plotly.graph_objs import Figure

from pdr_backend.lake_info.html_components import (
    alert_validation_error,
    fallback_badge,
    get_overview_summary,
    get_types_table,
    simple_badge,
)

GRAPHABLE = ["pdr_predictions", "_temp_pdr_predictions"]


class HtmlRenderer:
    def __init__(self, lake_info, table_views_overview, validation_overview):
        self.lake_info = lake_info
        self.table_views_overview = table_views_overview
        self.validation_overview = validation_overview

    def _filter_table(self, info_key, table_name, filter_value):
        df = getattr(self.table_views_overview, info_key)[table_name]

        if not filter_value:
            return df.limit(100)

        result = self.table_views_overview.get_filtered_result(table_name, filter_value)

        return result

    def get_graph_xy(self, table_name: str) -> Tuple[str, List[str]]:
        # TODO: define graphable columns for each table, extend list of graphable tables
        if table_name in ["pdr_predictions", "_temp_pdr_predictions"]:
            return "timestamp", ["stake", "payout"]

        raise ValueError(
            f"Table {table_name} not supported for graphing but in GRAPHABLE!"
        )

    def get_figure(
        self, table_name: str, filter_value: None, small: bool = False
    ) -> Figure:

        filtered_df = self._filter_table("table_info", table_name, filter_value)
        x, ys = self.get_graph_xy(table_name)

        figure = Figure(
            [
                go.Scatter(x=filtered_df[x], y=filtered_df[y], mode="lines", name=y)
                for y in ys
            ]
        )

        if small:
            figure.update_layout(margin={"t": 0, "l": 0, "b": 0, "r": 0})
            figure.update_xaxes(showticklabels=False)
            figure.update_yaxes(showticklabels=False)
            figure.update_layout(
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1,
                }
            )

        return figure

    def get_graph_info(self, table_name: str, filter_value: None):
        if table_name not in GRAPHABLE:
            return []

        small_fig = self.get_figure(table_name, filter_value, True)
        large_fig = self.get_figure(table_name, filter_value)

        modal = html.Div(
            [
                dcc.Graph(
                    figure=small_fig,
                    id=f"graph_small_{table_name}",
                    style={"height": "200px", "width": "100%"},
                ),
                dbc.Button(
                    "View larger", id=f"open_{table_name}", n_clicks=0, size="sm"
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle(f"Table {table_name} (filters may apply)")
                        ),
                        dbc.ModalBody(
                            dcc.Graph(figure=large_fig, id=f"graph_large_{table_name}"),
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close",
                                id=f"close_{table_name}",
                                className="ms-auto",
                                n_clicks=0,
                            )
                        ),
                    ],
                    id=f"modal_{table_name}",
                    is_open=False,
                    size="xl",
                ),
            ],
            style={"margin-bottom": "20px"},
        )

        return [modal]

    def get_side_info(self, info_key: str, table_name: str):
        result = []
        df = getattr(self.table_views_overview, info_key)[table_name]
        has_timestamp = any(col.name == "timestamp" for col in df.iter_columns())

        types_table = get_types_table(df)
        result.append(types_table)

        if has_timestamp:
            min_badge = fallback_badge("Min timestamp:", df["timestamp"].min())
            max_badge = fallback_badge("Max timestamp:", df["timestamp"].max())

            result += [min_badge, max_badge]

        nrows_badge = simple_badge("Number of rows:", df.shape[0])
        result.append(html.Div(nrows_badge, style={"margin-bottom": "10px"}))

        return result

    def _get_main_info(
        self, info_key: str, table_name: str, filter_value: Optional[str] = None
    ):
        if not filter_value:
            table_type = "Preview:"
        else:
            table_type = "Results (ltd. to 100 rows):"

        filtered_df = self._filter_table(info_key, table_name, filter_value)

        table = dbc.Table.from_dataframe(
            filtered_df.to_pandas(),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="small",
        )

        return [html.Strong(table_type), table]

    def get_main_info(
        self,
        info_key: str,
        table_name: str,
    ):
        # add callback ids as wrappers here
        return html.Div(
            children=self._get_main_info(info_key, table_name),
            id=f"tinfo_{info_key}_{table_name}",
        )

    def html_table_info(self, info_key: str):
        if not getattr(self.table_views_overview, info_key):
            return [html.Div("No tables found")]

        result = []
        for table_name in getattr(self.table_views_overview, info_key):
            graph_info = self.get_graph_info(table_name, None)
            side_info = self.get_side_info(info_key, table_name)
            main_info = self.get_main_info(info_key, table_name)

            result.append(
                dbc.Tab(
                    label=table_name,
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(graph_info + side_info, width=3),
                                dbc.Col(main_info, width=9),
                            ],
                        ),
                    ],
                )
            )

        return dbc.Tabs(children=result, style={"margin-top": "10px"})

    def validation_report(self):
        accordion_items = []
        active_items = []

        for i, key in enumerate(self.validation_overview.validation_results.keys()):
            violations = self.validation_overview.validation_results[key]
            if violations:
                active_items.append(f"item-{i}")

            accordion_items.append(
                dbc.AccordionItem(
                    [alert_validation_error(violation) for violation in violations],
                    title=(
                        f"{key} - {len(violations)} violation(s)"
                        if violations
                        else f"{key} - OK!"
                    ),
                )
            )

        return dbc.Accordion(
            accordion_items,
            always_open=True,
            active_item=active_items,
            style={"margin-top": "10px"},
        )

    def summary_overview(self):
        return get_overview_summary(self.table_views_overview.table_info)

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
                            label="Summary overview",
                            children=self.summary_overview(),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
                        ),
                        dbc.Tab(
                            label="Table Info",
                            children=self.html_table_info("table_info"),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
                        ),
                        dbc.Tab(
                            label="View Info",
                            children=self.html_table_info("view_info"),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
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


def get_callbacks(html_renderer, app):
    outputs = []

    for info_key in ["table_info", "view_info"]:
        outputs += [
            Output(f"tinfo_{info_key}_{table_name}", "children")
            for table_name in getattr(html_renderer.table_views_overview, info_key, [])
        ]

    for size in ["small", "large"]:
        outputs += [
            Output(f"graph_{size}_{table_wrapper_id}", "figure")
            for table_wrapper_id in GRAPHABLE
        ]

    @app.callback(
        outputs,
        Input("userFilter", "value"),
    )
    def filter_tables_and_graphs(filter_value):
        results = []

        for output in callback_context.outputs_list:
            output_id = output["id"]

            if "tinfo" in output_id:
                # it is a table output, has tinfo_ as a prefix
                info_key = "table_info" if "table_info" in output_id else "view_info"
                table_name = output_id.replace(f"tinfo_{info_key}_", "")

                results.append(
                    html_renderer._get_main_info(info_key, table_name, filter_value)
                )
            else:
                # it is a graph output
                table_name = (
                    output_id.replace("graph_", "")
                    .replace("small_", "")
                    .replace("large_", "")
                )

                results.append(
                    html_renderer.get_figure(
                        table_name, filter_value, "small" in output_id
                    )
                )

        return results

    for table_wrapper_id in GRAPHABLE:

        @app.callback(
            # pylint: disable=cell-var-from-loop
            Output(f"modal_{table_wrapper_id}", "is_open"),
            [
                # pylint: disable=cell-var-from-loop
                Input(f"open_{table_wrapper_id}", "n_clicks"),
                # pylint: disable=cell-var-from-loop
                Input(f"close_{table_wrapper_id}", "n_clicks"),
            ],
            # pylint: disable=cell-var-from-loop
            [State(f"modal_{table_wrapper_id}", "is_open")],
        )
        def toggle_modal(n1, n2, is_open):
            if n1 or n2:
                return not is_open
            return is_open
