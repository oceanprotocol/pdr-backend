#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from enum import Enum
from typing import Optional, Type, Union

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("table")


class TableType(Enum):
    PROD = "PROD"
    NEW_EVENTS = "NEW_EVENTS"
    UPDATE_EVENTS = "UPDATE_EVENTS"
    TEMP = "TEMP"
    TEMP_UPDATE = "TEMP_UPDATE"


@enforce_types
def is_etl_table(table_name: str) -> bool:
    table_name = table_name.removeprefix("_")
    table_name = table_name.removeprefix("temp_")

    for prefix in [TableType]:
        table_name = table_name.removeprefix(str(prefix).lower() + "_")

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


@enforce_types
class Table:
    def __init__(self, table_name: str, table_type: TableType = TableType.PROD):
        self.table_type = table_type
        self._base_table_name = table_name
        self._dataclass: Union[None, Type["LakeMapper"]] = None

    @property
    def table_name(self) -> str:
        table_type_mapping = {
            TableType.NEW_EVENTS: "_new_events_",
            TableType.UPDATE_EVENTS: "_update_events_",
            TableType.TEMP: "_temp_",
            TableType.TEMP_UPDATE: "_temp_update_",
        }
        
        return table_type_mapping.get(self.table_type, "") + self._base_table_name

    @property
    def dataclass(self) -> Type[LakeMapper]:
        if self._dataclass:
            return self._dataclass

        raise AttributeError("dataclass not set")

    @staticmethod
    def from_dataclass(
        dataclass: Type[LakeMapper], table_type: Optional[TableType] = None
    ) -> "Table":
        if not table_type:
            table_type = TableType.PROD

        db_table = Table(dataclass.get_lake_table_name(), table_type)
        db_table._dataclass = dataclass
        return db_table

    @enforce_types
    def append_to_storage(self, data: pl.DataFrame, ppss):
        self._append_to_csv(data, ppss)
        self._append_to_db(data, ppss)

    @enforce_types
    def _append_to_csv(self, data: pl.DataFrame, ppss):
        """
        Append the data from the DataFrame object into the CSV file
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        csvds = CSVDataStore.from_table(self, ppss)
        csvds.write(
            data,
            schema=self.dataclass.get_lake_schema(),
        )
        logger.info(
            "  Saved %s rows to csv files: %s", data.shape[0], self._base_table_name
        )

    @enforce_types
    def _append_to_db(self, data: pl.DataFrame, ppss):
        """
        Append the data from the DataFrame object into the database
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        DuckDBDataStore(ppss.lake_ss.lake_dir).insert_from_df(data, self.table_name)
        logger.info(
            "  Appended %s rows to db table: %s", data.shape[0], self.table_name
        )


class NewEventsTable(Table):
    def __init__(self, table_name: str):
        super().__init__(table_name, TableType.NEW_EVENTS)

    @staticmethod
    # type: ignore[override]
    # pylint: disable=arguments-differ
    def from_dataclass(dataclass: Type[LakeMapper]) -> "NewEventsTable":
        table = NewEventsTable(dataclass.get_lake_table_name())
        table._dataclass = dataclass
        return table


class UpdateEventsTable(Table):
    def __init__(self, table_name: str):
        super().__init__(table_name, TableType.UPDATE_EVENTS)

    @staticmethod
    # type: ignore[override]
    # pylint: disable=arguments-differ
    def from_dataclass(dataclass: Type[LakeMapper]) -> "UpdateEventsTable":
        table = UpdateEventsTable(dataclass.get_lake_table_name())
        table._dataclass = dataclass
        return table


class TempTable(Table):
    def __init__(self, table_name: str):
        super().__init__(table_name, TableType.TEMP)

    @staticmethod
    # type: ignore[override]
    # pylint: disable=arguments-differ
    def from_dataclass(dataclass: Type[LakeMapper]) -> "TempTable":
        table = TempTable(dataclass.get_lake_table_name())
        table._dataclass = dataclass
        return table


class TempUpdateTable(Table):
    def __init__(self, table_name: str):
        super().__init__(table_name, TableType.TEMP_UPDATE)

    @staticmethod
    # type: ignore[override]
    # pylint: disable=arguments-differ
    def from_dataclass(dataclass: Type[LakeMapper]) -> "TempUpdateTable":
        table = TempUpdateTable(dataclass.get_lake_table_name())
        table._dataclass = dataclass
        return table
