# The PersistentDataStore class is a subclass of the Base
import os
import glob

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.base_data_store import BaseDataStore


class PersistentDataStore(BaseDataStore):
    """
    A class to store and retrieve persistent data.
    """

    def __init__(self, base_directory: str):
        """
        Initialize a PersistentDataStore instance.
        @arguments:
            base_directory - The base directory to store the persistent data.
        """
        super().__init__(base_directory)

    @enforce_types
    def _create_and_fill_table(
        self, df: pl.DataFrame, dataset_identifier: str
    ):  # pylint: disable=unused-argument
        """
        Create the dataset and insert data to the persistent dataset.
        @arguments:
            df - The Polars DataFrame to append.
            dataset_identifier - A unique identifier for the dataset.
        """

        view_name = self._generate_view_name(dataset_identifier)

        # self.duckdb_conn.register(view_name, df)
        # Create the table
        self.duckdb_conn.execute(f"CREATE TABLE {view_name} AS SELECT * FROM df")

    @enforce_types
    def insert_to_table(self, df: pl.DataFrame, dataset_identifier: str):
        """
        Insert data to an persistent dataset.
        @arguments:
            df - The Polars DataFrame to append.
            dataset_identifier - A unique identifier for the dataset.
        @example:
            df = pl.DataFrame({
                "id": [1, 2, 3],
                "name": ["John", "Jane", "Doe"],
                "age": [25, 30, 35]
            })
            insert_to_table(df, "people")
        """

        view_name = self._generate_view_name(dataset_identifier)
        # Check if the table exists
        tables = self.duckdb_conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()

        if view_name in [table[0] for table in tables]:
            self.duckdb_conn.execute(f"INSERT INTO {view_name} SELECT * FROM df")
        else:
            self._create_and_fill_table(df, dataset_identifier)

    @enforce_types
    def query_data(
        self, dataset_identifier: str, query: str, partition_type: None = None
    ) -> pl.DataFrame:
        """
        Execute a SQL query across the persistent dataset using DuckDB.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            query - The SQL query to execute.
        @returns:
            pl.DataFrame - The result of the query.
        @example:
            query_data("people", "SELECT * FROM {view_name}")
        """

        view_name = self._generate_view_name(dataset_identifier)
        result_df = self.duckdb_conn.execute(query.format(view_name=view_name)).df()

        return pl.DataFrame(result_df)

    @enforce_types
    def drop_table(self, dataset_identifier: str, ds_type: str = "table"):
        """
        Drop the persistent dataset.
        @arguments:
            dataset_identifier - A unique identifier for the dataset.
            ds_type - The type of the dataset to drop. Either "table" or "view".
        @example:
            drop_table("people")
        """

        if ds_type not in ["view", "table"]:
            raise ValueError("ds_type must be either 'view' or 'table'")

        view_name = self._generate_view_name(dataset_identifier)
        self.duckdb_conn.execute(f"DROP {ds_type} {view_name}")

    @enforce_types
    def fill_from_csv_destination(self, csv_folder_path: str, dataset_identifier: str):
        """
        Fill the persistent dataset from CSV files.
        @arguments:
            csv_folder_path - The path to the folder containing the CSV files.
            dataset_identifier - A unique identifier for the dataset.
        @example:
            fill_from_csv_destination("data/csv", "people")
        """

        csv_files = glob.glob(os.path.join(csv_folder_path, "*.csv"))

        print("csv_files", csv_files)
        for csv_file in csv_files:
            df = pl.read_csv(csv_file)
            self.insert_to_table(df, dataset_identifier)

    @enforce_types
    def update_data(
        self, df: pl.DataFrame, dataset_identifier: str, identifier_column: str
    ):
        """
        Update the persistent dataset with the provided DataFrame.
        @arguments:
            df - The Polars DataFrame to update.
            dataset_identifier - A unique identifier for the dataset.
            identifier_column - The column to use as the identifier for the update.
        @example:
            df = pl.DataFrame({
                "id": [1, 2, 3],
                "name": ["John", "Jane", "Doe"],
                "age": [25, 30, 35]
            })
            update_data(df, "people", "id")
        """

        view_name = self._generate_view_name(dataset_identifier)
        update_columns = ", ".join(
            [f"{column} = {df[column]}" for column in df.columns]
        )
        self.duckdb_conn.execute(
            f"""UPDATE {view_name} 
            SET {update_columns} 
            WHERE {identifier_column} = {df[identifier_column]}"""
        )