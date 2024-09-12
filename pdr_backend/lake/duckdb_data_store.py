#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

# The DuckDBDataStore class is a subclass of the Base
import glob
import logging
import os
from typing import Any, Optional

import duckdb
import polars as pl
from enforce_typing import enforce_types
from polars._typing import SchemaDict

from pdr_backend.lake.base_data_store import BaseDataStore

logger = logging.getLogger("duckDB")


class _StoreInfo:
    duckdb_conn: Any

    @enforce_types
    def get_table_names(self, all_schemas: Optional[bool] = False):
        """
        Get the names of all tables from duckdb main schema.
        @returns:
            list - The names of the tables in the dataset.
        """
        where = " WHERE table_schema = 'main'" if not all_schemas else ""

        tables = self.duckdb_conn.execute(
            "SELECT table_name FROM information_schema.tables " + where
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
        view_names = [view[4] for view in views]
        return view_names

    @enforce_types
    def table_exists(self, table_name: str) -> bool:
        return table_name in self.get_table_names()

    @enforce_types
    def view_exists(self, view_name: str) -> bool:
        return view_name in self.get_view_names()

    @enforce_types
    def row_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.
        @arguments:
            table_name - The name of the table.
        @returns:
            int - The number of rows in the table.
        """
        return self.duckdb_conn.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[
            0
        ]  # type: ignore[index]


class _StoreCRUD:
    duckdb_conn: Any
    get_table_names: Any
    execute_sql: Any

    @enforce_types
    def create_empty(self, table_name: str, schema: SchemaDict):
        """
        Create a table if it does not exist.
        @arguments:
            table_name - The name of the table.
            schema - The schema of the table.
        @example:
            create_empty("people", {
                "id": pl.Int64,
                "name": pl.Utf8,
                "age": pl.Int64
            })
        """
        # check if the table exists
        table_names = self.get_table_names()

        if table_name not in table_names:
            # Create an empty DataFrame with the schema
            empty_df = pl.DataFrame([], schema=schema)
            self.create_from_df(empty_df, table_name)

    @enforce_types
    def create_from_df(
        self, df: pl.DataFrame, table_name: str
    ):  # pylint: disable=unused-argument
        """
        Create the table and insert data
        @arguments:
            df - The Polars DataFrame to append.
            table_name - A unique identifier for the dataset.
        """

        # Create the table
        self.execute_sql(f"CREATE TABLE {table_name} AS SELECT * FROM df")

    @enforce_types
    def insert_from_df(self, df: pl.DataFrame, table_name: str):
        """
        Insert data to a table
        @arguments:
            df - The Polars DataFrame to append.
            table_name - A unique table.
        @example:
            df = pl.DataFrame({
                "id": [1, 2, 3],
                "name": ["John", "Jane", "Doe"],
                "age": [25, 30, 35]
            })
            insert_from_df(df, "people")
        """
        # Check if the table exists
        table_names = self.get_table_names()

        if table_name in table_names:
            logger.info(
                "insert_to_table table_name = %s, num_rows = %s",
                table_name,
                df.shape[0],
            )
            self.duckdb_conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")
            return

        logger.info(
            "create_and_fill_table = %s, num_rows = %s", table_name, df.shape[0]
        )
        self.create_from_df(df, table_name)

    @enforce_types
    def insert_from_csv(self, table_name: str, csv_folder_path: str):
        """
        Insert to table from CSV files.
        @arguments:
            table_name - A unique name for the table.
            csv_folder_path - The path to the folder containing the CSV files.
        @example:
            insert_from_csv("data/csv", "people")
        """

        csv_files = glob.glob(os.path.join(csv_folder_path, "*.csv"))

        logger.info("csv_files %s", csv_files)
        for csv_file in csv_files:
            df = pl.read_csv(csv_file)
            self.insert_from_df(df, table_name)

    @enforce_types
    def move_table_data(self, from_table, to_table):
        """
        Move the table data from one table to another.
        @arguments:
            from_table - where we'll be taking data from
            to_table - wehere we'll be inserting data
        @example:
            move_table_data("temp_people", "people")
        """

        # Check if the table exists
        move_table_query = self.get_query_move_table_data(from_table, to_table)
        self.execute_sql(move_table_query)

    @enforce_types
    def update_data(self, df: pl.DataFrame, table_name: str, column_name: str):
        """
        Update the table with the provided DataFrame.
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
    def drop_table(self, table_name: str):
        """
        Drop the table.
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


class DuckDBDataStore(BaseDataStore, _StoreInfo, _StoreCRUD):
    """
    A class to store and retrieve persistent data.
    """

    @enforce_types
    def __init__(self, base_path: str, read_only: bool = False):
        """
        Initialize a DuckDBDataStore instance.
        @arguments:
            base_path - The base directory to store the persistent data.
        """
        super().__init__(base_path, read_only)
        self.duckdb_conn = duckdb.connect(
            database=f"{self.base_path}/duckdb.db", read_only=read_only
        )  # Keep a persistent connection

    @enforce_types
    def execute_sql(self, query: str):
        """
        Execute a SQL query across DuckDB using SQL.
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

    @enforce_types
    def query_data(self, query: str) -> Optional[pl.DataFrame]:
        """
        Execute a SQL query on DuckDB and return the result as a polars dataframe.
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

    def query_scalar(self, query: str) -> Any:
        """
        Execute a SQL query on DuckDB and return the result as a scalar.
        @arguments:
            query - The SQL query to execute.
        @returns:
            Any - The result of the query.
        @example:
            query_scalar("SELECT COUNT(*) FROM table_name")
        """
        result = self.duckdb_conn.execute(query).fetchone()

        if len(result) == 1:
            result = result[0]

        return result

    @enforce_types
    def get_query_drop_common_records_by_id(
        self, drop_table_name: str, ref_table_name: str
    ):
        """
        Builds the query string to perform the operation and returns it
        @arguments:
            drop_table_name - The table to drop records from.
            ref_table_name - The table to reference for the IDs to drop.
        @example:
            get_query_drop_common_records_by_id("bronze_pdr_slots", "update_pdr_slots")
        """

        # Return the query string
        return f"""
        DELETE FROM {drop_table_name}
        WHERE ID IN (
            SELECT DISTINCT ID
            FROM {ref_table_name}
        );
        """

    @enforce_types
    def get_query_move_table_data(self, from_table, to_table):
        """
        Builds the query string to perform the operation and returns it
        @arguments:
            from_table - where we'll be taking data from
            to_table - wehere we'll be inserting data
        @example:
            move_table_data("temp_people", "people")
        """

        # Check if the table exists
        table_names = self.get_table_names()
        assert (
            from_table.table_name in table_names
        ), f"Table {from_table.table_name} is "

        # check if the permanent table exists
        if to_table.table_name not in table_names:
            return f"CREATE TABLE {to_table.table_name} AS SELECT * FROM {from_table.table_name};"

        # Move the data from the temporary table to the permanent table
        return (
            f"INSERT INTO {to_table.table_name} SELECT * FROM {from_table.table_name};"
        )

    @enforce_types
    def export_tables_to_parquet_files(self):
        # Define the folder where exports will be saved
        export_folder_path = f"{self.base_path}/exports"
        tables = self.query_data("SHOW TABLES")["name"]

        # Ensure the export folder exists
        if not os.path.exists(export_folder_path):
            os.makedirs(export_folder_path)

        for table in tables:
            # Ensure the folder for each table exists
            table_folder_path = f"{export_folder_path}/{table}"
            if not os.path.exists(table_folder_path):
                os.makedirs(table_folder_path)

            # Get the maximum timestamp from Parquet files, if they exist
            try:
                max_timestamp_from_parquet = (
                    duckdb.execute(
                        f"SELECT MAX(timestamp) FROM '{table_folder_path}/*.parquet'"
                    ).fetchone()[0]
                    or 0
                )
            except Exception:
                # If no files or error, assume no data exported yet
                max_timestamp_from_parquet = 0

            # Get the maximum timestamp from the DuckDB table
            max_timestamp_from_db = (
                self.query_scalar(f"SELECT MAX(timestamp) FROM {table}") or 0
            )

            # If the database has no new data, skip this table
            if max_timestamp_from_db <= max_timestamp_from_parquet:
                continue

            # Define the Parquet file name based on the max timestamp from the DB
            parquet_file = f"{table}_{max_timestamp_from_db}.parquet"
            parquet_file_path = f"{table_folder_path}/{parquet_file}"

            # Export only new rows (i.e., with timestamps greater than the last export)
            query = f"""
            COPY (SELECT * FROM {table} WHERE timestamp > {max_timestamp_from_parquet})
            TO '{parquet_file_path}' (FORMAT 'parquet');
            """
            self.execute_sql(query)
