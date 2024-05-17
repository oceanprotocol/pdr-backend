from typing import Dict, List
from datetime import datetime

import polars as pl
from polars.dataframe.frame import DataFrame

from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.ppss.ppss import PPSS

pl.Config.set_tbl_hide_dataframe_shape(True)


class LakeInfo:
    def __init__(self, ppss: PPSS):
        self.pds = PersistentDataStore(ppss.lake_ss.lake_dir)
        self.all_table_names: List[str] = []
        self.table_info: Dict[str, DataFrame] = {}
        self.all_view_names: List[str] = []
        self.view_info: Dict[str, DataFrame] = {}

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

    def print_table_info(self, source_name: str, source: Dict[str, DataFrame]):
        table_summary = pl.DataFrame()

        for table_name in source:
            print("-" * 80)
            print("Columns for table {}:".format(table_name), end=" ")
            columns = []
            has_timestamp = False

            if len(source[table_name]) == 0:
                print("Table is empty. Please drop it.")
                continue

            for col in source[table_name].iter_columns():
                if col.name == "timestamp":
                    has_timestamp = True
                columns.append(f"{col.name}: {col.dtype}")

            print(",".join(columns))

            if has_timestamp:
                min_timestamp = source[table_name]["timestamp"].min()
                max_timestamp = source[table_name]["timestamp"].max()

                if isinstance(min_timestamp, (int, float)):
                    min_datestr = datetime.fromtimestamp(
                        min_timestamp / 1000.0
                    ).strftime("%d-%m-%Y %H:%M:%S")
                else:
                    min_datestr = None

                if isinstance(max_timestamp, (int, float)):
                    max_datestr = datetime.fromtimestamp(
                        max_timestamp / 1000.0
                    ).strftime("%d-%m-%Y %H:%M:%S")
                else:
                    max_datestr = None

                n_rows = len(source[table_name])

                if min_timestamp is not None:
                    print("Min timestamp: " + str(min_timestamp))
                if max_timestamp is not None:
                    print("Max timestamp: " + str(max_timestamp))

                if min_datestr is not None:
                    print("Min datestr: " + str(min_datestr))
                if max_datestr is not None:
                    print("Max datestr: " + str(max_datestr))

                if n_rows > 0:
                    print("Number of rows: {}".format(n_rows))

                table_info = pl.DataFrame(
                    {
                        "table_name": [table_name],
                        "n_rows": [n_rows],
                        "min_timestamp": [min_timestamp],
                        "max_timestamp": [max_timestamp],
                        "min_datestr": [min_datestr],
                        "max_datestr": [max_datestr],
                    }
                )
                table_summary = pl.concat([table_summary, table_info])
            else:
                print("No timestamp data")

            print("Preview")
            print(source[table_name])

        with pl.Config(tbl_rows=100):
            print("=" * 80)

            print("Summary - {}".format(source_name))
            print(table_summary)

    def run(self):
        self.generate()

        if len(self.all_table_names) == 0:
            print("No Lake Tables")
        else:
            print("Lake Tables:")
            print(self.all_table_names)
            self.print_table_info("tables", self.table_info)

        print("=" * 80)

        if len(self.all_view_names) == 0:
            print("Great - No views in Lake.")
        else:
            print("Lake Views:")
            print(self.all_view_names)
            self.print_table_info("views", self.view_info)
