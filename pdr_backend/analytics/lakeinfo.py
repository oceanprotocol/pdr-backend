from typing import Dict, List

import polars as pl
from polars.dataframe.frame import DataFrame

from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.ppss.ppss import PPSS

pl.Config.set_tbl_hide_dataframe_shape(True)


class LakeInfo:
    def __init__(self, ppss: PPSS):
        self.pds = PersistentDataStore(ppss.lake_ss.lake_dir, read_only=True)
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

            print("Preview: \n")
            print(source[table_name])

    def run(self):
        self.generate()
        print("Lake Tables:")
        print(self.all_table_names)
        self.print_table_info(self.table_info)

        print("=" * 80)
        print("Lake Views:")
        print(self.all_view_names)
        self.print_table_info(self.view_info)
