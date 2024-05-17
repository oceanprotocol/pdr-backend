from typing import Dict

from polars.dataframe.frame import DataFrame


class CliRenderer:
    def __init__(self, lake_info):
        self.lake_info = lake_info

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

    def show(self):
        print("Lake Tables:")
        print(self.lake_info.all_table_names)
        self.print_table_info(self.lake_info.table_info)

        print("=" * 80)
        print("Lake Views:")
        print(self.lake_info.all_view_names)
        self.print_table_info(self.lake_info.view_info)
