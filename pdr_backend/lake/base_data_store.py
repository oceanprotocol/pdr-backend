from abc import abstractmethod

import duckdb
from enforce_typing import enforce_types


class BaseDataStore:
    @enforce_types
    def __init__(self, base_directory=str):
        """
        Initialize a DataStore instance.
        @arguments:
            base_directory - The base directory to store the partitioned Parquet files.
        """

        self.base_directory = base_directory
        self.duckdb_conn = duckdb.connect(
            database=f"{self.base_directory}/duckdb.db"
        )  # Keep a persistent connection

    @abstractmethod
    def query_data(self, query: str):
        pass
