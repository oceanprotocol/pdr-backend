import logging
from typing import Optional
import polars as pl
from polars.type_aliases import SchemaDict

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.persistent_data_store import PersistentDataStore

logger = logging.getLogger("table")


@enforce_types
class Table:
    def __init__(self, table_name: str, df_schema: SchemaDict, ppss: PPSS):
        self.ppss = ppss
        self.table_name = table_name
        self.df_schema = df_schema
        self.df = pl.DataFrame([], schema=df_schema)
        print("self.df", self.df)
        self.csv_data_store = CSVDataStore(self.ppss.lake_ss.parquet_dir)
        self.PDS = PersistentDataStore(self.ppss.lake_ss.parquet_dir)

        self.load()

    @enforce_types
    def load(self):
        """
        Read the data from the Parquet file into a DataFrame object
        """
        print(f"Loading data for {self.table_name}")

        self.df = pl.DataFrame([], schema=self.df_schema)
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
        self.PDS.insert_to_table(data, self.table_name)
        n_new = data.shape[0]
        print(
            f"  Just saved df with {n_new} df rows to the database of {self.table_name}"
        )

    def get_pds_last_record(self) -> Optional[pl.DataFrame]:
        """
        Get the last record from the persistent data store

        @returns
            pl.DataFrame
        """

        query = f"SELECT * FROM {self.table_name} ORDER BY timestamp DESC LIMIT 1"
        try:
            return self.PDS.query_data(query)
        except Exception as e:
            print(f"Error fetching last record from PDS: {e}")
            return None
