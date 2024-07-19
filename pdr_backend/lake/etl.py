#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import time
from typing import Dict, List, Optional, Tuple

from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.gql_data_factory import (
    GQLDataFactory,
    _GQLDF_REGISTERED_TABLE_NAMES,
)
from pdr_backend.lake.table import (
    Table,
    TempTable,
    NewEventsTable,
    UpdateEventsTable,
    TempUpdateTable,
)
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.time_types import UnixTimeMs

from pdr_backend.lake.sql_etl_predictions import _do_sql_predictions
from pdr_backend.lake.sql_etl_payouts import _do_sql_payouts
from pdr_backend.lake.sql_etl_bronze_predictions import _do_sql_bronze_predictions


logger = logging.getLogger("etl")


# Registered ETL queries & tables
_ETL_REGISTERED_LAKE_TABLES = [BronzePrediction]

_ETL_REGISTERED_TABLE_NAMES = [
    t.get_lake_table_name() for t in _ETL_REGISTERED_LAKE_TABLES
]

_ETL_REGISTERED_QUERIES = [
    _do_sql_predictions,
    _do_sql_payouts,
    _do_sql_bronze_predictions,
]


class ETL:
    """
    @description
        The ETL class is responsible for performing the ETL process on the lake
        The ETL process is broken into 2 steps:
            1. Sync: Fetch data from data_factory
            2. Bronze: Build bronze tables

        The ETL class is meant to be kept around in memory and in it's own process.
        To access data/lake, use the table objects.
    """

    @enforce_types
    def __init__(self, ppss: PPSS, gql_data_factory: GQLDataFactory):
        self.ppss = ppss
        self.gql_data_factory = gql_data_factory

        # ETL uses ppss and it's own internal fns for checkpoints
        # Use this to clamp checkpoints to ppss
        self._clamp_checkpoints_to_ppss = False

    def _drop_temp_sql_tables(self):
        """
        @description
            Check if the etl temp tables are built
            If exists, drop them
        """
        # drop the tables if it exists
        db = DuckDBDataStore(self.ppss.lake_ss.lake_dir)
        for dataclass in _ETL_REGISTERED_LAKE_TABLES:
            table_name = dataclass.get_lake_table_name()
            db.drop_table(TempTable(table_name).table_name)
            db.drop_table(NewEventsTable(table_name).table_name)
            db.drop_table(UpdateEventsTable(table_name).table_name)
            db.drop_table(TempUpdateTable(table_name).table_name)

    def _do_bronze_swap_to_prod_atomic(self):
        """
        @description
            Merge the bronze ETL tables against prod database
            This needs to become a single transaction per table
            Such that it remains atomic, and is able to resume if it fails
        """
        db = DuckDBDataStore(self.ppss.lake_ss.lake_dir)

        bronze_tables = [BronzePrediction]
        for table in bronze_tables:
            prod_table = Table.from_dataclass(table)
            new_events_table = NewEventsTable.from_dataclass(table)
            update_events_table = UpdateEventsTable.from_dataclass(table)
            temp_update_table = TempUpdateTable.from_dataclass(table)

            if not db.table_exists(update_events_table.table_name):
                continue

            # Insert new records into live tables
            # We don't know if the table exists or not, so get the query string
            temp_to_prod_query = db.get_query_move_table_data(
                new_events_table, prod_table
            )

            # We'll also get the query string from the helper
            drop_records_from_table_by_id_query = (
                db.get_query_drop_records_from_table_by_id(
                    prod_table.table_name, temp_update_table.table_name
                )
            )

            # Here, the table needs to exist. So we'll build our own insert statement.
            temp_update_to_prod_query = f"""
            INSERT INTO {prod_table.table_name} SELECT * FROM {temp_update_table.table_name};
            """

            # We then need to drop the rows after all the ETL is complete
            cleanup_query = f"""
            DROP TABLE IF EXISTS {new_events_table.table_name};
            DROP TABLE IF EXISTS {update_events_table.table_name};
            DROP TABLE IF EXISTS {temp_update_table.table_name};
            """

            # Assemble and execute final transaction
            final_query = f"""
            {temp_to_prod_query}
            {drop_records_from_table_by_id_query}
            {temp_update_to_prod_query}
            {cleanup_query}
            """

            db.execute_sql(final_query)

    def do_etl(self):
        """
        @description
            Run the ETL process
        """

        st_ts = time.time_ns() / 1e9
        logger.info(">>>> REQUIRED ETL - do_etl - Start ETL.")

        try:
            # Drop any build tables if they already exist
            self._drop_temp_sql_tables()
            logger.info("do_etl - Drop build tables.")

            # Sync data
            self.gql_data_factory._update()
            logger.info("do_etl - Synced data. Start bronze_step.")

            self.do_bronze_step()

            end_ts = time.time_ns() / 1e9
            logger.info("do_etl - Completed bronze_step in %s sec.", end_ts - st_ts)

            # Move data to live at end of ETL
            self._do_bronze_swap_to_prod_atomic()

            logger.info(
                "do_etl - Moved build tables to permanent tables. ETL Complete."
            )
        except Exception as e:
            logger.info("Error when executing ETL: %s", e)

    def do_bronze_step(self):
        """
        @description
            We have updated our lake's raw data
            Now, let's build the bronze tables
            key tables: [bronze_pdr_predictions]
        """
        logger.info(">>>> REQUIRED ETL - do_bronze_step - Build bronze tables.")

        # Update bronze tables
        # let's keep track of time passed so we can log how long it takes for this step to complete
        st_ts = time.time_ns() / 1e9

        self.do_bronze_queries()

        end_ts = time.time_ns() / 1e9
        logger.info(
            ">>>> REQUIRED ETL - do_bronze_step - Completed in %s sec.", end_ts - st_ts
        )

    @enforce_types
    def _get_max_timestamp_values_from(
        self, tables: List[Table]
    ) -> Dict[str, Optional[UnixTimeMs]]:
        """
        @description
            Get the max timestamp values from the tables

        @arguments
            table_names - The list of table names to get the max timestamp values from
            table_type - The type of table to get the max timestamp values from
        @returns
            values - The max timestamp values from the tables
        """
        max_timestamp_query = (
            "SELECT '{}' as table_name, MAX(timestamp) as max_timestamp FROM {}"
        )

        all_db_tables = DuckDBDataStore(self.ppss.lake_ss.lake_dir).get_table_names()

        queries = []

        for table in tables:
            if table.table_name not in all_db_tables:
                logger.info(
                    "_get_max_timestamp_values_from - Table %s does not exist.",
                    table.table_name,
                )
                continue

            queries.append(
                max_timestamp_query.format(table.table_name, table.table_name)
            )

        table_names = [table.table_name for table in tables]
        none_values: Dict[str, Optional[UnixTimeMs]] = {
            table_name: None for table_name in table_names
        }

        if len(queries) == 0:
            return none_values

        final_query = " UNION ALL ".join(queries)
        result = DuckDBDataStore(self.ppss.lake_ss.lake_dir).query_data(final_query)

        if result is None:
            return none_values

        values: Dict[str, Optional[UnixTimeMs]] = {}

        for row in result.rows(named=True):
            table_name = row["table_name"]
            max_timestamp = row["max_timestamp"]

            values[table_name] = UnixTimeMs(max_timestamp) if max_timestamp else None

        return values

    @enforce_types
    def get_timestamp_values(
        self, table_names: List[str], default_timestr: str
    ) -> UnixTimeMs:
        max_timestamp_values = self._get_max_timestamp_values_from(
            [Table(tb) for tb in table_names]
        )

        # check if all values are None in max_timestamp_values
        # and return the default_timestr if so
        if all(value is None for value in max_timestamp_values.values()):
            return UnixTimeMs.from_timestr(default_timestr)

        values = []
        if len(max_timestamp_values) > 0:
            values = [
                value for value in max_timestamp_values.values() if value is not None
            ]

        timestamp = (
            max(values) if len(values) > 0 else UnixTimeMs.from_timestr(default_timestr)
        )
        return timestamp

    @enforce_types
    def _calc_bronze_start_end_ts(self) -> Tuple[UnixTimeMs, UnixTimeMs]:
        """
        @description
            Calculate the start and end timestamps for the bronze tables
            ETL updates should use from_timestamp by calculating
            max(etl_tables_max_timestamp).
            ETL updates should use to_timestamp by calculating
            min(max(source_tables_max_timestamp)).

        @flags
            use self._clamp_checkpoints_to_ppss operate ETL manually with ppss
            this skips checkpoint calculations
        """
        if self._clamp_checkpoints_to_ppss:
            return self.ppss.lake_ss.st_timestamp, self.ppss.lake_ss.fin_timestamp

        from_timestamp = self.get_timestamp_values(
            _ETL_REGISTERED_TABLE_NAMES, self.ppss.lake_ss.st_timestr
        )

        to_timestamp = self.get_timestamp_values(
            _GQLDF_REGISTERED_TABLE_NAMES, self.ppss.lake_ss.fin_timestr
        )

        assert from_timestamp <= to_timestamp, (
            f"from_timestamp ({from_timestamp}) must be less than or equal to "
            f"to_timestamp ({to_timestamp})"
        )

        return from_timestamp, to_timestamp

    def do_bronze_queries(self):
        """
        @description
            Run all bronze queries to process new + update events
        """
        logger.info("do_bronze_queries - start")

        # st_timestamp and fin_timestamp should be valid UnixTimeMS
        st_timestamp, fin_timestamp = self._calc_bronze_start_end_ts()
        db = DuckDBDataStore(self.ppss.lake_ss.lake_dir)

        # if st_ts or fin_ts != ppss, then we must have records somewhere
        is_first_run: bool = self._clamp_checkpoints_to_ppss is True or (
            st_timestamp == self.ppss.lake_ss.st_timestamp
            and fin_timestamp == self.ppss.lake_ss.fin_timestamp
        )

        print(">>>> is_first_run", is_first_run)

        for etl_query in _ETL_REGISTERED_QUERIES:
            etl_query(
                db=db, st_ms=st_timestamp, fin_ms=fin_timestamp, first_run=is_first_run
            )

            logger.info(
                "do_bronze_queries - completed query %s",
                etl_query,
            )
