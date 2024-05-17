from typing import Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import Dash, html
from polars.dataframe.frame import DataFrame

from pdr_backend.util.time_types import UnixTimeMs


class HtmlRenderer:
    def __init__(self, lake_info):
        self.lake_info = lake_info

    def html_table_info(
        self, source: Dict[str, DataFrame], violations: Optional[List[str]] = None
    ):
        result = []

        if violations is None:
            violations = []

        alerts = [
            dbc.Alert(
                [html.I(className="bi bi-x-octagon-fill me-2"), violation],
                color="danger",
                className="d-flex align-items-center",
            )
            for violation in violations
        ]

        if not source:
            return alerts

        for table_name in source:
            table_1_result = []
            table_2_result = []
            has_timestamp = False

            types = []
            for col in source[table_name].iter_columns():
                if col.name == "timestamp":
                    has_timestamp = True

                types.append(html.Tr([html.Td(str(col.name)), html.Td(str(col.dtype))]))

            types_table = dbc.Table(types, bordered=True)
            table_1_result.append(
                html.Div(
                    [html.Strong("Schema"), types_table],
                )
            )

            if has_timestamp:
                min_timestamp = source[table_name]["timestamp"].min()
                max_timestamp = source[table_name]["timestamp"].max()

                if isinstance(min_timestamp, (int, float)):
                    min_datestr = UnixTimeMs(min_timestamp).to_timestr()
                else:
                    min_datestr = None

                if isinstance(max_timestamp, (int, float)):
                    max_datestr = UnixTimeMs(max_timestamp).to_timestr()
                else:
                    max_datestr = None

                min_badge = fallback_badge("Min timestamp:", min_timestamp, min_datestr)
                max_badge = fallback_badge("Max timestamp:", max_timestamp, max_datestr)

                table_1_result.append(html.Div([min_badge, max_badge]))

            shape = source[table_name].shape
            nrows_badge = simple_badge("Number of rows:", shape[0])
            table_1_result.append(
                html.Div(nrows_badge, style={"margin-bottom": "10px"})
            )

            table = dbc.Table.from_dataframe(
                source[table_name].limit(100).to_pandas(),
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="small",
            )
            table_2_result.append(html.Div([html.Strong("Preview:"), table]))

            result.append(
                dbc.Tab(
                    label=table_name,
                    children=[
                        dbc.Row([dbc.Col(alerts)]),
                        dbc.Row(
                            [
                                dbc.Col(table_1_result, width=3),
                                dbc.Col(table_2_result, width=9),
                            ],
                        ),
                    ],
                )
            )

        return dbc.Tabs(children=result, style={"margin-top": "10px"})

    def show(self):
        app = Dash(
            __name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
        )

        # TODO: should we add all the validations here? or only those corresponding to the tabs?
        all_violations = (
            self.lake_info.validate_expected_table_names()
            + self.lake_info.validate_expected_view_names()
        )
        total_violations = len(all_violations)
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
                dbc.Tabs(
                    [
                        dbc.Tab(
                            label="Table Info",
                            children=self.html_table_info(
                                self.lake_info.table_info,
                                self.lake_info.validate_expected_table_names(),
                            ),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
                        ),
                        dbc.Tab(
                            label="View Info",
                            children=self.html_table_info(
                                self.lake_info.view_info,
                                self.lake_info.validate_expected_view_names(),
                            ),
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


def fallback_badge(text, value, nat_str):
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
