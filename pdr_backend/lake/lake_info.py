from typing import Dict, List

import dash_bootstrap_components as dbc
import polars as pl
from dash import Dash, html
from polars.dataframe.frame import DataFrame

from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.time_types import UnixTimeMs

pl.Config.set_tbl_hide_dataframe_shape(True)


class LakeInfo:
    def __init__(self, ppss: PPSS, use_html: bool = False):
        self.pds = PersistentDataStore(ppss.lake_ss.lake_dir, read_only=True)
        self.all_table_names: List[str] = []
        self.table_info: Dict[str, DataFrame] = {}
        self.all_view_names: List[str] = []
        self.view_info: Dict[str, DataFrame] = {}
        self.html = use_html

    def generate(self):
        self.all_table_names = self.pds.get_table_names(all_schemas=True)

        for table_name in self.all_table_names:
            self.table_info[table_name] = self.pds.query_data(
                "SELECT * FROM {}".format(table_name)
            )

        self.all_view_names = self.pds.get_view_names()

        for view_name in self.all_view_names:
            self.view_info[view_name] = self.pds.query_data(
                "SELECT * FROM {}".format(view_name)
            )

    def print_table_info(self, source: Dict[str, DataFrame]):
        for table_name in source:
            print("-" * 80)
            print("Columns for table {}:".format(table_name), end=" ")
            columns = []
            has_timestamp = False

            for col in source[table_name].iter_columns():
                if col.name == "timestamp":
                    has_timestamp = True
                columns.append(f"{col.name}: {col.dtype}")

            print(",".join(columns))

            if has_timestamp:
                max_timestamp = source[table_name]["timestamp"].max()
                if max_timestamp is not None:
                    print("Max timestamp: " + str(max_timestamp))
                else:
                    print("No timestamp data")

            shape = source[table_name].shape
            print(f"Number of rows: {shape[0]}")

            print("Data: \n")
            print(source[table_name])

    def html_table_info(self, source: Dict[str, DataFrame]):
        result = []
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
                    children=dbc.Row(
                        [
                            dbc.Col(table_1_result, width=3),
                            dbc.Col(table_2_result, width=9),
                        ],
                        style={"margin-top": "10px"},
                    ),
                )
            )

        return dbc.Tabs(children=result)

    def run(self):
        self.generate()

        if self.html:
            self.show_dashboard()
            return

        print("Lake Tables:")
        print(self.all_table_names)
        self.print_table_info(self.table_info)

        print("=" * 80)
        print("Lake Views:")
        print(self.all_view_names)
        self.print_table_info(self.view_info)

    def show_dashboard(self):
        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        app.layout = html.Div(
            [
                html.H2("Lake Tables"),
                dbc.Tabs(
                    [
                        dbc.Tab(
                            label="Table Info",
                            children=self.html_table_info(self.table_info),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
                        ),
                        dbc.Tab(
                            label="View Info",
                            children=self.html_table_info(self.view_info),
                            labelClassName="text-success",
                            style={"margin-top": "10px"},
                        ),
                    ]
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
