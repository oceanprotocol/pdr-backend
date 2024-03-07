import logging
import os
from typing import Dict
import polars as pl
from polars.type_aliases import SchemaDict

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.plutil import has_data, newest_ut
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.persistent_data_store import PersistentDataStore

logger = logging.getLogger("table")


@enforce_types
class Table:
    def __init__(self, table_name: str, df_schema: SchemaDict, ppss: PPSS):
        self.ppss = ppss
        self.table_name = table_name
        self.df_schema = df_schema
        
        self.csv_data_store = CSVDataStore(self.ppss.lake_ss.parquet_dir)
        self.persistent_data_store = PersistentDataStore(self.ppss.lake_ss.parquet_dir)

        self.df = pl.DataFrame([], schema=df_schema)
        print("self.df", self.df)

    def append_to_storage(self, data: pl.DataFrame):
        self._append_to_csv(data)
        self._append_to_db(data)

    def _append_to_csv(self, data: pl.DataFrame):
        """
        Append the data from the DataFrame object into the CSV file
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        self.csv_data_store.write(self.table_name, data, schema=self.df_schema)
        n_new = data.shape[0]
        print(
            f"  Just saved df with {n_new} df rows to the csv files of {self.table_name}"
        )

    def _append_to_db(self, data: pl.DataFrame):
        """
        Append the data from the DataFrame object into the database
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        self.persistent_data_store.insert_to_table(data, self.table_name)
        n_new = data.shape[0]
        print(
            f"  Just saved df with {n_new} df rows to the database of {self.table_name}"
        )
