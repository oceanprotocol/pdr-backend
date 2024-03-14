import logging
from typing import Optional
import polars as pl
from polars.type_aliases import SchemaDict

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.plutil import get_table_name

logger = logging.getLogger("table")


@enforce_types
class Table:
    def __init__(self, table_name: str, df_schema: SchemaDict, ppss: PPSS):
        self.ppss = ppss
        self.table_name = table_name
        self.df_schema = df_schema

        self.base_path = self.ppss.lake_ss.parquet_dir

    @enforce_types
    def append_to_storage(self, data: pl.DataFrame, build_mode: bool = False):
        self._append_to_csv(data)
        self._append_to_db(data, build_mode)

    @enforce_types
    def _append_to_csv(self, data: pl.DataFrame):
        """
        Append the data from the DataFrame object into the CSV file
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        csvds = CSVDataStore(self.base_path)
        print(f" csvds = {csvds}")
        csvds.write(self.table_name, data, schema=self.df_schema)
        n_new = data.shape[0]
        print(
            f"  Just saved df with {n_new} df rows to the csv files of {self.table_name}"
        )

    @enforce_types
    def _append_to_db(self, data: pl.DataFrame, build_mode: bool = False):
        """
        Append the data from the DataFrame object into the database
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        table_name = get_table_name(self.table_name, build_mode)
        PersistentDataStore(self.base_path).insert_to_table(data, table_name)
        n_new = data.shape[0]
        print(f"  Just saved df with {n_new} df rows to the database of {table_name}")

    def get_pds_last_record(self) -> Optional[pl.DataFrame]:
        """
        Get the last record from the persistent data store

        @returns
            pl.DataFrame
        """

        query = f"SELECT * FROM {self.table_name} ORDER BY timestamp DESC LIMIT 1"
        try:
            return PersistentDataStore(self.base_path).query_data(query)
        except Exception as e:
            print(f"Error fetching last record from PDS: {e}")
            return None

    @enforce_types
    def get_records(
        self,
        source: Optional[str] = "db",
    ) -> Optional[pl.DataFrame]:
        """
        Get the records from the persistent data store

        @returns
            pl.DataFrame
        """
        if source == "db":
            return PersistentDataStore(self.base_path).query_data(
                f"SELECT * FROM {self.table_name}"
            )

        return CSVDataStore(self.base_path).read_all(
            self.table_name, schema=self.df_schema
        )
