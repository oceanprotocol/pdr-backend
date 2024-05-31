import inspect
import logging
from enum import Enum
from typing import Optional, Type, Union

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("table")


class TableType(Enum):
    NORMAL = "NORMAL"
    TEMP = "TEMP"
    ETL = "ETL"


@enforce_types
def is_etl_table(table_name: str) -> bool:
    table_name = table_name.removeprefix("_")
    table_name = table_name.removeprefix("temp_")
    table_name = table_name.removeprefix("_")
    table_name = table_name.removeprefix("etl_")
    table_name = table_name.removeprefix("temp_")

    return (
        table_name.startswith("bronze_")
        or table_name.startswith("silver_")
        or table_name.startswith("gold_")
    )


@enforce_types
def drop_tables_from_st(db: DuckDBDataStore, type_filter: str, st: UnixTimeMs):
    trunc_count = table_count = 0
    if type_filter not in ["raw", "etl"]:
        return

    table_names = db.get_table_names()

    for table_name in table_names:
        if type_filter == "etl" and not is_etl_table(table_name):
            logger.info(
                "[while dropping etl tables] skipping non-etl table %s", table_name
            )
            continue

        if type_filter == "raw" and is_etl_table(table_name):
            logger.info(
                "[while dropping raw tables] skipping non-raw table %s", table_name
            )
            continue

        logger.info(
            "[while dropping %s tables] drop table %s starting at %s",
            type_filter,
            table_name,
            st,
        )
        rows_before = db.row_count(table_name)
        logger.info("rows before: %s", rows_before)
        db.query_data(f"DELETE FROM {table_name} WHERE timestamp >= {st}")
        rows_after = db.row_count(table_name)
        logger.info("rows after: %s", rows_after)
        if rows_before != rows_after:
            table_count += 1
            trunc_count += rows_before - rows_after

    logger.info("truncated %s rows from %s tables", trunc_count, table_count)


def get_caller_ppss():
    caller_ppss = None
    prev_frame = inspect.currentframe()

    while caller_ppss is None and prev_frame is not None:
        prev_frame = prev_frame.f_back

        if not prev_frame:
            break

        # allow for "magical" ppss retrieval from tests
        if "test/" in prev_frame.f_code.co_filename:
            if prev_frame.f_locals.get("etl"):
                caller_ppss = prev_frame.f_locals["etl"].ppss
                break
            if prev_frame.f_locals.get("ppss"):
                caller_ppss = prev_frame.f_locals["ppss"]
                break

        # along the way, some caller of the NamedTable.from_dataclass() method
        # must have a ppss attribute
        if not prev_frame.f_locals.get("self"):
            continue

        caller = prev_frame.f_locals["self"]
        if hasattr(caller, "ppss"):
            caller_ppss = caller.ppss

    if not caller_ppss:
        raise ValueError("Could not find a PPSS object in the call stack")
    return caller_ppss


@enforce_types
class NamedTable:
    def __init__(self, table_name: str, table_type: TableType = TableType.NORMAL):
        self.table_name = table_name
        self.table_type = table_type
        self._dataclass: Union[None, Type["LakeMapper"]] = None
        self._ppss: Union[None, PPSS] = None

    @property
    def fullname(self) -> str:
        if self.table_type == TableType.TEMP:
            return f"_temp_{self.table_name}"
        if self.table_type == TableType.ETL:
            return f"_etl_{self.table_name}"

        return self.table_name

    @property
    def dataclass(self) -> Type[LakeMapper]:
        if self._dataclass:
            return self._dataclass

        raise AttributeError("dataclass not set")

    @property
    def ppss(self) -> PPSS:
        if self._ppss:
            return self._ppss

        raise AttributeError("ppss not set")

    @staticmethod
    def from_dataclass(
        dataclass: Type[LakeMapper], table_type: Optional[TableType] = None
    ) -> "NamedTable":
        if not table_type:
            table_type = TableType.NORMAL

        named_table = NamedTable(dataclass.get_lake_table_name(), table_type)
        named_table._dataclass = dataclass
        named_table._ppss = get_caller_ppss()
        return named_table

    @enforce_types
    def append_to_storage(self, data: pl.DataFrame):
        self._append_to_csv(data)
        self._append_to_db(data)

    @enforce_types
    def _append_to_csv(self, data: pl.DataFrame):
        """
        Append the data from the DataFrame object into the CSV file
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        csvds = CSVDataStore.from_table(self, self.ppss)
        logger.info(" csvds = %s", csvds)
        csvds.write(
            data,
            schema=self.dataclass.get_lake_schema(),
        )
        logger.info("  Saved %s rows to csv files: %s", data.shape[0], self.table_name)

    @enforce_types
    def _append_to_db(self, data: pl.DataFrame):
        """
        Append the data from the DataFrame object into the database
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        DuckDBDataStore(self.ppss.lake_ss.lake_dir).insert_to_table(data, self.fullname)
        logger.info("  Appended %s rows to db table: %s", data.shape[0], self.fullname)


class TempTable(NamedTable):
    def __init__(self, table_name: str):
        super().__init__(table_name, TableType.TEMP)

    @staticmethod
    # type: ignore[override]
    # pylint: disable=arguments-differ
    def from_dataclass(dataclass: Type[LakeMapper]) -> "TempTable":
        temp_table = TempTable(dataclass.get_lake_table_name())
        temp_table._dataclass = dataclass
        temp_table._ppss = get_caller_ppss()
        return temp_table


class ETLTable(NamedTable):
    def __init__(self, table_name: str):
        super().__init__(table_name, TableType.ETL)

    @staticmethod
    # type: ignore[override]
    # pylint: disable=arguments-differ
    def from_dataclass(dataclass: Type[LakeMapper]) -> "ETLTable":
        etl_table = ETLTable(dataclass.get_lake_table_name())
        etl_table._dataclass = dataclass
        etl_table._ppss = get_caller_ppss()
        return etl_table
