import hashlib
import os
import polars as pl
import duckdb
from enforce_typing import enforce_types


class PartitionedDataStore:
    @enforce_types
    def __init__(self, base_directory=str):
        self.base_directory = base_directory
        self.duckdb_conn = duckdb.connect(
            database=":memory:"
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

        hash_object = hashlib.md5(base_path.encode())
        return f"dataset_{hash_object.hexdigest()}"

    @enforce_types
    def append_data(self, df: pl.DataFrame, dataset_identifier: str):
        """
        Append data to an in-memory dataset.
        @arguments:
            df - The Polars DataFrame to append.
            dataset_identifier - A unique identifier for the dataset.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)
        # Register the DataFrame as an Arrow table temporarily
        # arrow_table = df.to_arrow()
        self.duckdb_conn.register(view_name, df)

    @enforce_types
    def finalize_data(self, dataset_identifier: str):
        """
        Finalizes the data by writing the in-memory dataset to partitioned Parquet files.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
        """

        view_name = self._generate_view_name(self.base_directory + dataset_identifier)
        query = f"SELECT * FROM {view_name}"
        result_df = self.duckdb_conn.execute(query).df()

        # Convert to Polars DataFrame for partitioned write
        df = pl.DataFrame(result_df)

        lazy_df = df.lazy()
        # Determine partitions based on a timestamp column, assuming 'timestamp' column exists
        lazy_df = lazy_df.with_columns(
            [pl.from_epoch("timestamp", time_unit="s").alias("date")]
        )
        df = lazy_df.collect()

        partitions = (
            lazy_df.select(
                pl.col("date").dt.year().alias("year"),
                pl.col("date").dt.month().alias("month"),
                pl.col("date").dt.day().alias("day"),
            )
            .unique()
            .collect()
        )

        for partition in partitions.rows():
            year, month, day = partition
            partition_path = os.path.join(
                self.base_directory,
                dataset_identifier,
                f"year={year}",
                f"month={month}",
            )
            os.makedirs(partition_path, exist_ok=True)
            partition_df = df.filter(
                (pl.col("date").dt.year() == year)
                & (pl.col("date").dt.month() == month)
            )
            file_path = os.path.join(partition_path, f"{day}.parquet")
            partition_df.write_parquet(file_path)

    @enforce_types
    def query_data(self, dataset_identifier: str, query: str) -> pl.DataFrame:
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
            f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{dataset_path}/*/*/*.parquet', hive_partitioning=1)" # pylint: disable=line-too-long
        )

        # Execute the provided SQL query
        result_df = self.duckdb_conn.execute(query.format(view_name=view_name)).df()

        return pl.DataFrame(result_df)
