# The PersistentDataStore class is a subclass of the Base
import logging
import os
import glob
from typing import Optional, Dict
import duckdb

from polars.datatypes import DataType, DataTypeClass
from polars.type_aliases import SchemaDict
from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.base_data_store import BaseDataStore

logger = logging.getLogger("pds")


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

        self.duckdb_data_types: Dict[DataTypeClass, str] = {
            pl.Int8: "TINYINT",  # TINYINT in SQL typically represents an 8-bit integer.
            pl.Int16: "SMALLINT",  # SMALLINT in SQL represents a 16-bit integer.
            pl.Int32: "INTEGER",  # INTEGER is commonly used in SQL.
            pl.Int64: "BIGINT",  # BIGINT in SQL represents a 64-bit integer.
            pl.UInt8: "TINYINT",  # For unsigned, DuckDB may handle this similarly; check specifics.
            pl.UInt16: "SMALLINT",  # Same note as above for unsigned small integer.
            pl.UInt32: "INTEGER",  # Same note as above for unsigned integer.
            pl.UInt64: "BIGINT",  # Same note as above for unsigned big integer.
            pl.Float32: "FLOAT",  # FLOAT in SQL.
            pl.Float64: "DOUBLE",  # DOUBLE in SQL for higher precision.
            pl.Boolean: "BOOLEAN",  # BOOLEAN is standard in SQL.
            pl.Utf8: "TEXT",  # TEXT for string data.
            pl.Date: "DATE",  # DATE only for date; TIMESTAMP if including time.
            pl.Datetime: "TIMESTAMP",  # TIMESTAMP for date and time.
            pl.Time: "TIME",  # TIME only for time data.
            pl.Duration: "INTERVAL",  # INTERVAL for time durations.
            pl.List: "ARRAY",  # ARRAY for list data types, ensure compatibility.
            pl.Object: "BLOB",  # BLOB for binary large objects, check usage context.
            pl.Struct: "STRUCT",  # STRUCT for nested data, might need specific handling in SQL.
            # Additional types like dictionaries, etc.,
            # can be added based on specific needs and compatibility.
        }

    def _get_sql_column_type(self, column_type) -> str:
        """
        Get the SQL column type from the Polars column type.
        @arguments:
            column_type - The Polars column type.
        @returns:
            str - The SQL column type.
        """
        return self.duckdb_data_types[column_type]

    @enforce_types
    def create_table_if_not_exists(self, table_name: str, schema: SchemaDict):
        """
        Create a table if it does not exist.
        @arguments:
            table_name - The name of the table.
            schema - The schema of the table.
        @example:
            create_table_if_not_exists("people", {
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
            self._create_and_fill_table(empty_df, table_name)

    def _create_sql_table_schema(self, schema: SchemaDict) -> str:
        """
        Create the SQL schema for the table.
        @arguments:
            schema - The schema of the table.
        @returns:
            str - The SQL schema for the table.
        """

        table_schema = ", ".join(
            [
                (
                    f"""{column} {self._get_sql_column_type(schema[column])}
                    {' UNIQUE' if column == 'ID' else ''}"""
                    if isinstance(schema[column], DataType)
                    else ""
                )
                for column in schema.keys()
            ]
        )

        return table_schema

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

        sql_table_schema = self._create_sql_table_schema(df.schema)
        # Create the table
        self.execute_sql(f"CREATE TABLE {table_name} ({sql_table_schema})")

        # Insert the data columns
        self.duckdb_conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")

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

        if table_name in table_names:
            logger.info("insert_to_table table_name = %s", table_name)
            logger.info("insert_to_table DF = %s", df)
            self.duckdb_conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")
            return

        logger.info("create_and_fill_table = %s", table_name)
        logger.info("create_and_fill_table DF = %s", df)
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
    def move_table_data(self, temp_table, permanent_table_name: str):
        """
        Move the table data from the temporary storage to the permanent storage.
        @arguments:
            temp_table - The temporary table object
            permanent_table_name - The name of the permanent table.
        @example:
            move_table_data("temp_people", "people")
        """

        # Check if the table exists
        table_names = self.get_table_names()

        if temp_table.fullname not in table_names:
            logger.info(
                "move_table_data - Table %s does not exist", temp_table.fullname
            )
            return

        # check if the permanent table exists
        if permanent_table_name not in table_names:
            # select one row from the temporary table
            temp_table_df = self.duckdb_conn.execute(
                f"SELECT * FROM {temp_table.fullname} LIMIT 1"
            ).pl()

            # create the sql schema
            sql_table_schema = self._create_sql_table_schema(temp_table_df.schema)

            # create the permanent table
            self.execute_sql(
                f"CREATE TABLE {permanent_table_name} ({sql_table_schema})"
            )

            # create table if it does not exist
            self.execute_sql(
                f"INSERT INTO {permanent_table_name} SELECT * FROM {temp_table.fullname}"
            )
            return

        # get temporary table columns
        temp_table_columns = self.duckdb_conn.execute(
            f"SELECT * FROM {temp_table.fullname} LIMIT 0"
        ).df()

        temp_table_columns = temp_table_columns.columns

        # generate on conflict clause
        on_conflict_columns = ", ".join(
            [
                f"{column} = EXCLUDED.{column}"
                for column in temp_table_columns
                if column != "ID"
            ]
        )
        # Move the data from the temporary table to the permanent table
        self.execute_sql(
            f"""INSERT INTO {permanent_table_name}
            SELECT * FROM {temp_table.fullname}
            ON CONFLICT (ID) DO UPDATE SET {on_conflict_columns}"""
        )

    @enforce_types
    def fill_table_from_csv(self, table_name: str, csv_folder_path: str):
        """
        Fill the persistent dataset from CSV files.
        @arguments:
            table_name - A unique name for the table.
            csv_folder_path - The path to the folder containing the CSV files.
        @example:
            fill_table_from_csv("data/csv", "people")
        """

        csv_files = glob.glob(os.path.join(csv_folder_path, "*.csv"))

        logger.info("csv_files %s", csv_files)
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
