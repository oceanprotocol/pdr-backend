from hashlib import md5
from abc import abstractmethod
from typing import Optional, Literal

import duckdb
from enforce_typing import enforce_types


class BaseDataStore:
    @enforce_types
    def __init__(self, base_directory=str):
        """
        Initialize a PartitionedDataStore instance.
        @arguments:
            base_directory - The base directory to store the partitioned Parquet files.
        """

        self.base_directory = base_directory
        self.duckdb_conn = duckdb.connect(
            database=f"{self.base_directory}/duckdb.db"
        )  # Keep a persistent connection

    @enforce_types
    def _generate_view_name(self, base_path=str) -> str:
        """
        Generate a unique view name for a given base path.
        @arguments:
            base_path - The base path to generate a view name for.
        @returns:
            str - A unique view name.
        """

        path = f"{self.base_directory}/{base_path}"
        hash_object = md5(path.encode())
        return f"dataset_{hash_object.hexdigest()}"

    @abstractmethod
    def query_data(
        self,
        dataset_identifier: str,
        query: str,
        partition_type: Optional[Literal["date", "address"]] = None,
    ):
        pass
