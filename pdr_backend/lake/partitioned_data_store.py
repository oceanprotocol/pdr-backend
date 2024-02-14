from typing import Literal

import hashlib
import os
import polars as pl
import duckdb
from enforce_typing import enforce_types

class PartitionedDataStore:
    @enforce_types
    def __init__(self, base_directory=str):
        """
        Initialize a PartitionedDataStore instance.
        @arguments:
            base_directory - The base directory to store the partitioned Parquet files.
        """

        self.base_directory = base_directory
        self.duckdb_conn = duckdb.connect(
            database=":memory:"
        )  # Keep a persistent connection
        self.partition_patterns = {
            "date": "/year=*/month=*/day=*/*.parquet",
            "address": "/address=*/*.parquet",
        }

    @enforce_types
    def _generate_view_name(self, base_path=str) -> str:
        """
        Generate a unique view name for a given base path.
        @arguments:
            base_path - The base path to generate a view name for.
        @returns:
            str - A unique view name.
        """

        hash_object = hashlib.md5(base_path.encode())
        return f"dataset_{hash_object.hexdigest()}"

    @enforce_types
    def create_and_fill_table(self, df: pl.DataFrame, dataset_identifier: str):
        """
        Create the dataset and insert data to the in-memory dataset.
        @arguments:
            df - The Polars DataFrame to append.
            dataset_identifier - A unique identifier for the dataset.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)
        # Register the DataFrame as an Arrow table temporarily
        # arrow_table = df.to_arrow()
        self.duckdb_conn.register(view_name, df)

    @enforce_types
    def insert_to_table(self, df: pl.DataFrame, dataset_identifier: str):
        """
        Insert data to an in-memory dataset.
        @arguments:
            df - The Polars DataFrame to append.
            dataset_identifier - A unique identifier for the dataset.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)
        # Check if the table exists
        tables = self.duckdb_conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()

        if view_name in [table[0] for table in tables]:
            values_str = ", ".join(
                [
                    f"({', '.join([str(x) for x in row])})"
                    for row in df.rows()
                ]
            )
            self.duckdb_conn.execute(f"INSERT INTO {view_name} VALUES {values_str}")
        else:
            self.create_and_fill_table(df, dataset_identifier)

    @enforce_types
    def create_view_and_query_data(self, dataset_identifier: str, query: str) -> pl.DataFrame:
        """
        Execute a SQL query across partitioned Parquet files using DuckDB.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            query - The SQL query to execute. The query must contain a {view_name} placeholder.

        @returns:
            pl.DataFrame - The result of the query.
        """

        dataset_path = os.path.join(self.base_directory, dataset_identifier)
        view_name = self._generate_view_name(dataset_path)

        # DuckDB automatically recognizes the partition scheme when reading from a directory
        self.duckdb_conn.execute(
            f"""CREATE OR REPLACE VIEW {view_name} AS 
            SELECT * FROM read_parquet(
                '{dataset_path}{self.partition_patterns["date"]}', 
                hive_partitioning=1
            )"""
        )

        # Execute the provided SQL query
        result_df = self.duckdb_conn.execute(query.format(view_name=view_name)).df()

        return pl.DataFrame(result_df)

    @enforce_types
    def query_data(
        self,
        dataset_identifier: str,
        query: str,
        partition_type: Literal["date", "address"]
    ) -> pl.DataFrame:
        """
            Execute a SQL query directly on partitioned Parquet files using DuckDB.
                @arguments:
                    dataset_identifier - A unique identifier for the dataset.
                    query - The SQL query to execute. 
                        The query must contain a {dataset_path} placeholder.

                @returns:
                    pl.DataFrame - The result of the query.
        """

        dataset_path = os.path.join(self.base_directory, dataset_identifier)

        # DuckDB automatically recognizes the partition scheme when reading from a directory
        result_df = self.duckdb_conn.execute(
            query.format(dataset_path=f"""
                         read_parquet(
                            '{dataset_path}{self.partition_patterns[partition_type]}', 
                            hive_partitioning=1
                         )""")
        ).df()

        return pl.DataFrame(result_df)

    @enforce_types
    def _export_data_with_address_hive(self, dataset_identifier: str, address_column: str):
        """
        Finalizes the data by writing the in-memory dataset to partitioned
        Parquet files using the COPY command.
        The data is partitioned by the Ethereum address.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            address_column - The name of the column containing the Ethereum addresses.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)

        # Use the COPY command to write the data to the partitioned Parquet files
        self.duckdb_conn.execute(f"""COPY (
                                     SELECT *, {address_column} FROM {view_name}
                                ) TO '{self.base_directory}' 
                                (
                                    FORMAT PARQUET, 
                                    PARTITION BY ({address_column}), 
                                    OVERWRITE=TRUE
                                )"""
                                )

    @enforce_types
    def _export_data_with_date_hive(self, dataset_identifier: str, date_column: str = "timestamp"):
        """
        Finalizes the data by writing the in-memory dataset to 
        partitioned Parquet files using the COPY command.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)

        # Use the COPY command to write the data to the partitioned Parquet files
        self.duckdb_conn.execute(
            f"""COPY (
                    SELECT *, 
                    EXTRACT(year FROM {date_column}) as year, 
                    EXTRACT(month FROM {date_column}) as month, 
                    EXTRACT(day FROM {date_column}) as day FROM {view_name}
                ) TO '{self.base_directory}' 
                (FORMAT PARQUET, 
                PARTITION BY (year, month, day), 
                OVERWRITE=TRUE)"""
            )
    
    @enforce_types
    def _export_to_target(self, dataset_identifier: str, output_path: str):
        """
        Export the in-memory dataset to a single Parquet file.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            output_path - The path to the output Parquet file.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)
        self.duckdb_conn.execute(f"COPY {view_name} TO '{output_path}' (FORMAT PARQUET)")

    @enforce_types
    def export_to_parquet(
        self,
        dataset_identifier: str,
        output_path: str = None,
        partition_type: Literal["date", "address"] = "date",
        partition_column: str = None
    ):
        """
        Finalizes the data by writing the in-memory dataset to partitioned Parquet files.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            output_path - The path to the output Parquet file.
            partition_type - The type of partitioning to use.
            partition_column - The name of the column to partition by.
        """

        if partition_type == "date":
            self._export_data_with_date_hive(dataset_identifier, partition_column)
        elif partition_type == "address":
            self._export_data_with_address_hive(dataset_identifier, partition_column)
        else:
            self._export_to_target(dataset_identifier, output_path)
