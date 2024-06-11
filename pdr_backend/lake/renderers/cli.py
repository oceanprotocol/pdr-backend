from typing import Dict

import polars as pl
from polars.dataframe.frame import DataFrame

from pdr_backend.util.time_types import UnixTimeMs


class CliRenderer:
    def __init__(self, lake_info):
        self.lake_info = lake_info

    def print_table_info(self, source_name: str, source: Dict[str, DataFrame]):
        table_summary = DataFrame()

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
                    min_datestr = UnixTimeMs(min_timestamp).to_timestr()
                else:
                    min_datestr = None

                if isinstance(max_timestamp, (int, float)):
                    max_datestr = UnixTimeMs(max_timestamp).to_timestr()
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

                table_info = DataFrame(
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

    def show(self):
        if len(self.lake_info.all_table_names) == 0:
            print("No Lake Tables")
        else:
            print("Lake Tables:")
            print(self.lake_info.all_table_names)
            self.print_table_info("tables", self.lake_info.table_info)

        if len(self.lake_info.all_view_names) == 0:
            print("Great - No views in Lake.")
        else:
            print("=" * 80)
            print("Lake Views:")
            print(self.lake_info.all_view_names)
            self.print_table_info("views", self.lake_info.view_info)
