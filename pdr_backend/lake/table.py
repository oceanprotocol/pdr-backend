from enum import Enum
import logging
import polars as pl
from polars.type_aliases import SchemaDict

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.persistent_data_store import PersistentDataStore

logger = logging.getLogger("table")


class TableType(Enum):
    NORMAL = "NORMAL"
    TEMP = "TEMP"
    ETL = "ETL"


@enforce_types
def get_table_name(table_name: str, table_type: TableType = TableType.NORMAL) -> str:
    """
    Get the table name with the build mode prefix
    """
    if table_type == TableType.TEMP:
        return f"_temp_{table_name}"
    if table_type == TableType.ETL:
        return f"_etl_{table_name}"
    return table_name


@enforce_types
class Table:
    def __init__(self, table_name: str, df_schema: SchemaDict, ppss: PPSS):
        self.ppss = ppss
        self.table_name = table_name
        self.df_schema = df_schema

        self.base_path = self.ppss.lake_ss.lake_dir

    @enforce_types
    def append_to_storage(
        self, data: pl.DataFrame, table_type: TableType = TableType.NORMAL
    ):
        self._append_to_csv(data)
        self._append_to_db(data, table_type)

    @enforce_types
    def _append_to_csv(self, data: pl.DataFrame):
        """
        Append the data from the DataFrame object into the CSV file
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        csvds = CSVDataStore(self.base_path)
        logger.info(" csvds = %s", csvds)
        csvds.write(self.table_name, data, schema=self.df_schema)
        logger.info("  Saved %s rows to csv files: %s", data.shape[0], self.table_name)

    @enforce_types
    def _append_to_db(
        self, data: pl.DataFrame, table_type: TableType = TableType.NORMAL
    ):
        """
        Append the data from the DataFrame object into the database
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        table_name = get_table_name(self.table_name, table_type)
        PersistentDataStore(self.base_path).insert_to_table(data, table_name)
        logger.info("  Appended %s rows to db table: %s", data.shape[0], table_name)


@enforce_types
class NamedTable:
    def __init__(self, table_name: str, table_type: TableType = TableType.NORMAL):
        self.table_name = table_name
        self.table_type = table_type

    @property
    def fullname(self) -> str:
        return get_table_name(self.table_name, self.table_type)


class TempTable(NamedTable):
    def __init__(self, table_name: str):
        super().__init__(table_name, TableType.TEMP)
