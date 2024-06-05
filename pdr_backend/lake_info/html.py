from typing import Dict, List, Optional

import dash_bootstrap_components as dbc
import polars as pl
from dash import Dash, Input, Output, html
from polars.dataframe.frame import DataFrame

from pdr_backend.lake_info.html_components import (
    alert_validation_error,
    alert_validation_ok,
    fallback_badge,
    get_types_table,
    simple_badge,
)
from pdr_backend.lake_info.overview import TableViewsOverview, ValidationOverview
from pdr_backend.util.time_types import UnixTimeMs


class HtmlRenderer:
    def __init__(self, lake_info, table_views_overview, validation_overview):
        self.lake_info = lake_info
        self.table_views_overview = table_views_overview
        self.validation_overview = validation_overview

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
        df = getattr(self.table_views_overview, info_key)[table_name]

        if not filter_value:
            table_type = "Preview:"
            filtered_df = df.limit(100)
        else:
            table_type = "Results (ltd. to 100 rows):"
            filtered_df = self.table_views_overview.get_filtered_result(
                table_name, filter_value
            )

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
            side_info = self.get_side_info(info_key, table_name)
            main_info = self.get_main_info(info_key, table_name)

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
            alerts = [alert_validation_error(violation) for violation in violations]

            if not alerts:
                alerts = [alert_validation_ok(key)]

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
    table_wrapper_ids = []

    for info_key in ["table_info", "view_info"]:
        for table_name in getattr(html_renderer.table_views_overview, info_key):
            table_wrapper_ids.append(f"tinfo_{info_key}_{table_name}")

    for table_wrapper_id in table_wrapper_ids:

        @app.callback(
            Output(table_wrapper_id, "children"),
            Input("userFilter", "value"),
        )
        def filter_tables(filter_value):
            info_key = table_wrapper_id.split("_")[1] + "_info"
            table_name = table_wrapper_id[
                table_wrapper_id.index(info_key) + len(info_key) + 1 :
            ]
            return html_renderer._get_main_info(info_key, table_name, filter_value)
