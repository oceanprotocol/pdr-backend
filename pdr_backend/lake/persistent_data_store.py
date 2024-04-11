# The PersistentDataStore class is a subclass of the Base
import os
import glob
from typing import Optional
import duckdb

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.base_data_store import BaseDataStore


class PersistentDataStore(BaseDataStore):
    """
    A class to store and retrieve persistent data.
    """

    @enforce_types
    def __init__(self, base_path: str, read_only: bool = False):
        """
        Initialize a PersistentDataStore instance.
        @arguments:
            base_path - The base directory to store the persistent data.
        """
        super().__init__(base_path, read_only)
        self.duckdb_conn = duckdb.connect(
            database=f"{self.base_path}/duckdb.db", read_only=read_only
        )  # Keep a persistent connection

    @enforce_types
    def _create_and_fill_table(
        self, df: pl.DataFrame, table_name: str
    ):  # pylint: disable=unused-argument
        """
        Create the table and insert data
        @arguments:
            df - The Polars DataFrame to append.
            dataset_identifier - A unique identifier for the dataset.
        """

        # Create the table
        self.execute_sql(f"CREATE TABLE {table_name} AS SELECT * FROM df")

    @enforce_types
    def get_table_names(self):
        """
        Get the names of all tables from duckdb main schema.
        @returns:
            list - The names of the tables in the dataset.
        """
        tables = self.duckdb_conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()

        return [table[0] for table in tables]

    @enforce_types
    def get_view_names(self):
        """
        Get the names of all views from duckdb main schema.
        @returns:
            list - The views inside duckdb main schema.
        """

        views = self.duckdb_conn.execute("SELECT * FROM duckdb_views;").fetchall()

        return [views]

    @enforce_types
    def insert_to_table(self, df: pl.DataFrame, table_name: str):
        """
        Insert data to an persistent dataset.
        @arguments:
            df - The Polars DataFrame to append.
            table_name - A unique table.
        @example:
            df = pl.DataFrame({
                "id": [1, 2, 3],
                "name": ["John", "Jane", "Doe"],
                "age": [25, 30, 35]
            })
            insert_to_table(df, "people")
        """

        # Check if the table exists
        table_names = self.get_table_names()

        print(f"insert_to_table table_name = {table_name}")
        print(f"insert_to_table DF = {df}")
        if table_name in table_names:
            self.execute_sql(f"INSERT INTO {table_name} SELECT * FROM df")
        else:
            self._create_and_fill_table(df, table_name)

    @enforce_types
    def query_data(self, query: str) -> Optional[pl.DataFrame]:
        """
        Execute a SQL query across the persistent dataset using DuckDB.
        @arguments:
            table_name - A unique name for the table.
            query - The SQL query to execute.
        @returns:
            pl.DataFrame - The result of the query.
        @example:
            query_data("SELECT * FROM table_name")
        """

        try:
            result_df = self.duckdb_conn.execute(query).pl()
            return result_df
        except duckdb.CatalogException as e:
            if "Table" in str(e) and "not exist" in str(e):
                return None
            raise e

    @enforce_types
    def drop_table(self, table_name: str):
        """
        Drop the persistent table.
        @arguments:
            table_name - A unique name for the table.
        @example:
            drop_table("pdr_predictions")
        """
        # Drop the table if it exists
        self.execute_sql(f"DROP TABLE IF EXISTS {table_name}")

    @enforce_types
    def drop_view(self, view_name: str):
        """
        Drop the view.
        @arguments:
            view_name - A unique name for the view.
        @example:
            drop_view("_etl_pdr_predictions")
        """
        # Drop the table if it exists
        self.execute_sql(f"DROP VIEW IF EXISTS {view_name}")

    @enforce_types
    def move_table_data(self, temp_table_name: str, permanent_table_name: str):
        """
        Move the table data from the temporary storage to the permanent storage.
        @arguments:
            temp_table_name - The name of the temporary table.
            permanent_table_name - The name of the permanent table.
        @example:
            move_table_data("temp_people", "people")
        """

        # Check if the table exists
        table_names = self.get_table_names()

        if temp_table_name in table_names:
            # check if the permanent table exists
            if permanent_table_name not in table_names:
                # create table if it does not exist
                self.execute_sql(
                    f"CREATE TABLE {permanent_table_name} AS SELECT * FROM {temp_table_name}"
                )
            else:
                # Move the data from the temporary table to the permanent table
                self.execute_sql(
                    f"INSERT INTO {permanent_table_name} SELECT * FROM {temp_table_name}"
                )
        else:
            print(f"move_table_data - Table {temp_table_name} does not exist")

    @enforce_types
    def fill_from_csv_destination(self, csv_folder_path: str, table_name: str):
        """
        Fill the persistent dataset from CSV files.
        @arguments:
            csv_folder_path - The path to the folder containing the CSV files.
            table_name - A unique name for the table.
        @example:
            fill_from_csv_destination("data/csv", "people")
        """

        csv_files = glob.glob(os.path.join(csv_folder_path, "*.csv"))

        print("csv_files", csv_files)
        for csv_file in csv_files:
            df = pl.read_csv(csv_file)
            self.insert_to_table(df, table_name)

    @enforce_types
    def update_data(self, df: pl.DataFrame, table_name: str, column_name: str):
        """
        Update the persistent dataset with the provided DataFrame.
        @arguments:
            df - The Polars DataFrame to update.
            table_name - A unique name for the table.
            column_name - The column to use as the index for the update.
        @example:
            df = pl.DataFrame({
                "id": [1, 2, 3],
                "name": ["John", "Jane", "Doe"],
                "age": [25, 30, 35]
            })
            update_data(df, "people", "id")
        """

        update_columns = ", ".join(
            [f"{column} = {df[column]}" for column in df.columns]
        )
        self.execute_sql(
            f"""UPDATE {table_name} 
            SET {update_columns} 
            WHERE {column_name} = {df[column_name]}"""
        )

    @enforce_types
    def execute_sql(self, query: str):
        """
        Execute a SQL query across the persistent dataset using DuckDB.
        @arguments:
            query - The SQL query to execute.
        @example:
            execute_sql("SELECT * FROM table_name")
        """

        # self._connect()

        # if self.duckdb_conn is None:
        #     raise Exception("DuckDB connection is not established")
        self.duckdb_conn.execute("BEGIN TRANSACTION")
        self.duckdb_conn.execute(query)
        self.duckdb_conn.execute("COMMIT")
