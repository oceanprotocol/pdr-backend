from typing import Optional

import os
import polars as pl

from enforce_typing import enforce_types
from pdr_backend.lake.base_data_store import BaseDataStore

# Maybe a base class
# PersistentDataStore (it will include only DuckDB)
# PartitionedDataStore (it will handle everything related to partitioned data *.parquet files)


class PartitionedDataStore(BaseDataStore):
    """
    A class to manage partitioned Parquet files using DuckDB.
    """

    @enforce_types
    def __init__(self, base_directory=str):
        """
        Initialize a PartitionedDataStore instance.
        @arguments:
            base_directory - The base directory to store the partitioned Parquet files.
        """

        super().__init__(base_directory)

        self.partition_patterns = {
            "date": "/year=*/month=*/day=*/*.parquet",
            "address": "/address=*/*.parquet",
        }

    @enforce_types
    def create_view_and_query_data(
        self, dataset_identifier: str, query: str
    ) -> pl.DataFrame:
        """
        Avoid to use it if it is not necessary. It is better to use the query_data method.
        Execute a SQL query across partitioned Parquet files using DuckDB.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            query - The SQL query to execute. The query must contain a {view_name} placeholder.

        @returns:
            pl.DataFrame - The result of the query.

        @example:
            create_view_and_query_data(
                "transactions",
                "SELECT * FROM {view_name} WHERE value > 1000"
            )
        """

        dataset_path = os.path.join(self.base_directory, dataset_identifier)
        view_name = self._generate_view_name(dataset_path)

        # check if the query is valid
        if "{view_name}" not in query:
            raise ValueError("query must contain a {view_name} placeholder")

        temp_view_name = f"temp_{view_name}"
        # DuckDB automatically recognizes the partition scheme when reading from a directory
        self.duckdb_conn.execute(
            f"""CREATE OR REPLACE VIEW {temp_view_name} AS 
            SELECT * FROM read_parquet(
                '{dataset_path}{self.partition_patterns["date"]}', 
                hive_partitioning=1
            )"""
        )

        # Execute the provided SQL query
        result_df = self.duckdb_conn.execute(
            query.format(view_name=temp_view_name)
        ).df()

        # DROP the view to free up memory / disk space
        self.duckdb_conn.execute(f"DROP VIEW {temp_view_name}")

        return pl.DataFrame(result_df)

    @enforce_types
    def query_data(
        self,
        dataset_identifier: str,
        query: str,
        partition_type: Optional[str] = "date",
    ) -> pl.DataFrame:
        """
        Execute a SQL query directly on partitioned Parquet files using DuckDB.
            @arguments:
                dataset_identifier - A unique identifier for the dataset.
                query - The SQL query to execute.
                    The query must contain a {dataset_path} placeholder.

            @returns:
                pl.DataFrame - The result of the query.

            @example:
                query_data(
                    "transactions",
                    "SELECT * FROM {dataset_path} WHERE value > 1000",
                    "date"
                )
        """
        if partition_type not in ["date", "address"]:
            raise ValueError("partition_type must be either 'date' or 'address'")

        # check if the query is valid
        if "{dataset_path}" not in query:
            raise ValueError("query must contain a {dataset_path} placeholder")

        dataset_path = os.path.join(self.base_directory, dataset_identifier)

        # DuckDB automatically recognizes the partition scheme when reading from a directory
        result_df = self.duckdb_conn.execute(
            query.format(
                dataset_path=f"""
                         read_parquet(
                            '{dataset_path}{self.partition_patterns[partition_type]}', 
                            hive_partitioning=1
                         )"""
            )
        ).df()

        return pl.DataFrame(result_df)

    @enforce_types
    def _export_data_with_address_hive(
        self, dataset_identifier: str, address_column: str
    ):
        """
        Finalizes the data by writing the persistent dataset to partitioned
        Parquet files using the COPY command.
        The data is partitioned by the Ethereum address.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            address_column - The name of the column containing the Ethereum addresses.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)

        self.duckdb_conn.execute(
            f"""CREATE OR REPLACE VIEW processed_data AS 
            SELECT *, {address_column} FROM {view_name}"""
        )

        dataset_path = os.path.join(self.base_directory, dataset_identifier)

        if not os.path.exists(dataset_path):
            # Create the directory if it doesn't exist
            os.makedirs(dataset_path)

        copy_query = f"""
            COPY (
                SELECT * FROM processed_data
            )
            TO '{dataset_path}'
            (
                FORMAT PARQUET,
                PARTITION_BY ({address_column}),
                OVERWRITE_OR_IGNORE 1
            )"""

        # Use the COPY command to write the data to the partitioned Parquet files
        self.duckdb_conn.execute(copy_query)

        # DROP the view to free up memory / disk space
        self.duckdb_conn.execute("DROP VIEW processed_data")

    @enforce_types
    def _export_data_with_date_hive(
        self, dataset_identifier: str, date_column: str = "timestamp"
    ):
        """
        Finalizes the data by writing the persistent dataset to
        partitioned Parquet files using the COPY command.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
        """

        print("dataset_identifier", dataset_identifier)
        view_name = self._generate_view_name(self.base_directory + dataset_identifier)

        self.duckdb_conn.execute(
            f"""CREATE OR REPLACE VIEW processed_data AS 
            SELECT *, 
                DATE_PART('year', CAST({date_column} AS TIMESTAMP)) as year,
                DATE_PART('month', CAST({date_column} AS TIMESTAMP)) as month,
                DATE_PART('day', CAST({date_column} AS TIMESTAMP)) as day
            FROM {view_name}"""
        )

        dataset_path = os.path.join(self.base_directory, dataset_identifier)

        if not os.path.exists(dataset_path):
            # Create the directory if it doesn't exist
            os.makedirs(dataset_path)

        copy_query = f"""
            COPY (
                SELECT * FROM processed_data
            ) 
            TO '{dataset_path}' 
            (
                FORMAT PARQUET,
                PARTITION_BY (year, month, day),
                OVERWRITE_OR_IGNORE 1
            )"""

        # Use the COPY command to write the data to the partitioned Parquet files
        self.duckdb_conn.execute(copy_query)

        # DROP the view to free up memory / disk space
        self.duckdb_conn.execute("DROP VIEW processed_data")

    @enforce_types
    def _export_to_target(self, dataset_identifier: str, output_path: str):
        """
        Export the persistent dataset to a single Parquet file.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            output_path - The path to the output Parquet file.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)
        self.duckdb_conn.execute(
            f"COPY {view_name} TO '{output_path}' (FORMAT PARQUET)"
        )

    @enforce_types
    def export_to_parquet(
        self,
        dataset_identifier: str,
        output_path: Optional[str] = None,
        partition_type: Optional[str] = "date",
        partition_column: Optional[str] = None,
    ):
        """
        Finalizes the data by writing the persistent dataset to partitioned Parquet files.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            output_path - The path to the output Parquet file.
            partition_type - The type of partitioning to use.
            partition_column - The name of the column to partition by.
        @example:
            export_to_parquet("transactions", "data/transactions.parquet", "date")
        """
        if partition_type not in ["date", "address"]:
            raise ValueError("partition_type must be either 'date' or 'address'")

        if partition_type == "date":
            self._export_data_with_date_hive(dataset_identifier, partition_column)
        elif partition_type == "address":
            self._export_data_with_address_hive(dataset_identifier, partition_column)
        else:
            self._export_to_target(dataset_identifier, output_path)
