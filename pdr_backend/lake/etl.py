import logging
import time
from typing import Dict, List, Optional, Tuple
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.table import TableType, get_table_name, NamedTable, TempTable
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_table_name,
    bronze_pdr_predictions_schema,
    get_bronze_pdr_predictions_data_with_SQL,
)
from pdr_backend.lake.table_bronze_pdr_slots import (
    bronze_pdr_slots_table_name,
    bronze_pdr_slots_schema,
    get_bronze_pdr_slots_data_with_SQL,
)
from pdr_backend.lake.table_registry import TableRegistry
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.table_pdr_payouts import payouts_table_name
from pdr_backend.lake.table_pdr_predictions import predictions_table_name
from pdr_backend.lake.table_pdr_subscriptions import subscriptions_table_name
from pdr_backend.lake.table_pdr_slots import slots_table_name
from pdr_backend.lake.table_pdr_truevals import truevals_table_name
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("etl")


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

    def __init__(self, ppss: PPSS, gql_data_factory: GQLDataFactory):
        self.ppss = ppss
        self.gql_data_factory = gql_data_factory

        TableRegistry().register_tables(
            {
                bronze_pdr_predictions_table_name: (
                    bronze_pdr_predictions_table_name,
                    bronze_pdr_predictions_schema,
                    self.ppss,
                ),
                bronze_pdr_slots_table_name: (
                    bronze_pdr_slots_table_name,
                    bronze_pdr_slots_schema,
                    self.ppss,
                ),
            }
        )

        self.raw_table_names = [
            payouts_table_name,
            predictions_table_name,
            truevals_table_name,
            slots_table_name,
            subscriptions_table_name,
        ]

        self.bronze_table_getters = {
            bronze_pdr_predictions_table_name: get_bronze_pdr_predictions_data_with_SQL,
            bronze_pdr_slots_table_name: get_bronze_pdr_slots_data_with_SQL,
        }

        logger.info("self.bronze_table_getters: %s", self.bronze_table_getters)

        self.bronze_table_names = list(self.bronze_table_getters.keys())

        self.temp_table_names = []
        for table_name in self.bronze_table_names:
            self.temp_table_names.append(get_table_name(table_name, TableType.NORMAL))

    def _drop_temp_sql_tables(self):
        """
        @description
            Check if the etl temp tables are built
            If not, build them
            If exists, drop them and rebuild
        """
        # drop the tables if it exists
        pds = PersistentDataStore(self.ppss.lake_ss.lake_dir)
        for table_name in self.temp_table_names:
            pds.drop_table(get_table_name(table_name, TableType.TEMP))

    def _move_from_temp_tables_to_live(self):
        """
        @description
            Move the records from our ETL temporary build tables to live, in-production tables
        """

        pds = PersistentDataStore(self.ppss.lake_ss.lake_dir)
        for table_name in self.temp_table_names:
            logger.info("move table %s to live", table_name)
            pds.move_table_data(
                TempTable(table_name),
                table_name,
            )

            pds.drop_table(get_table_name(table_name, TableType.TEMP))
            pds.drop_view(get_table_name(table_name, TableType.ETL))

    def do_etl(self):
        """
        @description
            Run the ETL process
        """

        st_ts = time.time_ns() / 1e9
        logger.info("do_etl - Start ETL.")

        try:
            # Drop any build tables if they already exist
            self._drop_temp_sql_tables()
            logger.info("do_etl - Drop build tables.")

            # Sync data
            self.gql_data_factory.get_gql_tables()
            logger.info("do_etl - Synced data. Start bronze_step.")

            self.do_bronze_step()

            end_ts = time.time_ns() / 1e9
            logger.info("do_etl - Completed bronze_step in %s sec.", end_ts - st_ts)
            
            # At the end of the ETL pipeline, we want to
            # 1. move from TEMP tables to production tables
            # 2. drop TEMP tables and ETL views
            self._move_from_temp_tables_to_live()

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
            key tables: [bronze_pdr_predictions and bronze_pdr_slots]
        """
        logger.info("do_bronze_step - Build bronze tables.")

        # Update bronze tables
        # let's keep track of time passed so we can log how long it takes for this step to complete
        st_ts = time.time_ns() / 1e9

        self.update_bronze_pdr()

        end_ts = time.time_ns() / 1e9
        logger.info("do_bronze_step - Completed in %s sec.", end_ts - st_ts)

    def _get_max_timestamp_values_from(
        self, tables: List[NamedTable]
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

        all_db_tables = PersistentDataStore(
            self.ppss.lake_ss.lake_dir
        ).get_table_names()

        queries = []

        for table in tables:
            if table.fullname not in all_db_tables:
                logger.info(
                    "_get_max_timestamp_values_from - Table %s does not exist.",
                    table.fullname,
                )
                continue

            queries.append(max_timestamp_query.format(table.fullname, table.fullname))

        table_names = [table.fullname for table in tables]
        none_values: Dict[str, Optional[UnixTimeMs]] = {
            table_name: None for table_name in table_names
        }

        if len(queries) == 0:
            return none_values

        final_query = " UNION ALL ".join(queries)
        result = PersistentDataStore(self.ppss.lake_ss.lake_dir).query_data(final_query)

        logger.info("_get_max_timestamp_values_from - result: %s", result)

        if result is None:
            return none_values

        values: Dict[str, Optional[UnixTimeMs]] = {}

        for row in result.rows(named=True):
            table_name = row["table_name"]
            max_timestamp = row["max_timestamp"]

            values[table_name] = UnixTimeMs(max_timestamp)

        return values

    def get_timestamp_values(
        self, table_names: List[str], default_timestr: str
    ) -> UnixTimeMs:
        max_timestamp_values = self._get_max_timestamp_values_from(
            [NamedTable(tb, TableType.NORMAL) for tb in table_names]
        )
        values = []
        if len(max_timestamp_values) > 0:
            values = [
                value for value in max_timestamp_values.values() if value is not None
            ]
        timestamp = (
            min(values) if len(values) > 0 else UnixTimeMs.from_timestr(default_timestr)
        )
        return timestamp

    def _calc_bronze_start_end_ts(self) -> Tuple[UnixTimeMs, UnixTimeMs]:
        """
        @description
            Calculate the start and end timestamps for the bronze tables
            ETL updates should use from_timestamp by calculating
            max(etl_tables_max_timestamp).
            ETL updates should use to_timestamp by calculating
            min(max(source_tables_max_timestamp)).
        """
        from_timestamp = self.get_timestamp_values(
            self.bronze_table_names, self.ppss.lake_ss.st_timestr
        )

        to_timestamp = self.get_timestamp_values(
            self.raw_table_names, self.ppss.lake_ss.fin_timestr
        )

        assert from_timestamp <= to_timestamp, (
            f"from_timestamp ({from_timestamp}) must be less than or equal to "
            f"to_timestamp ({to_timestamp})"
        )

        return from_timestamp, to_timestamp

    @enforce_types
    def create_etl_view(self, table_name: str):
        # Assemble view query and create the view
        assert (
            table_name in self.bronze_table_names
        ), f"{table_name} must be a bronze table"

        pds = PersistentDataStore(self.ppss.lake_ss.lake_dir)
        temp_table_name = get_table_name(table_name, TableType.TEMP)
        etl_view_name = get_table_name(table_name, TableType.ETL)

        table_exists = pds.table_exists(table_name)
        temp_table_exists = pds.table_exists(temp_table_name)
        etl_view_exists = pds.view_exists(etl_view_name)
        assert temp_table_exists, f"{temp_table_name} must already exist"
        if etl_view_exists:
            logger.error("%s must not exist", etl_view_name)
            return

        view_query = None

        if table_exists and temp_table_exists:
            view_query = """
                CREATE VIEW {} AS
                (
                    SELECT * FROM {}
                    UNION ALL
                    SELECT * FROM {}
                )""".format(
                etl_view_name,
                table_name,
                temp_table_name,
            )
            pds.query_data(view_query)
            logger.info("  Created %s view using %s table and %s temp table", etl_view_name, table_name, temp_table_name)
        else:
            view_query = (
                f"CREATE VIEW {etl_view_name} AS SELECT * FROM {temp_table_name}"
            )
            pds.query_data(view_query)
            logger.info("  Created %s view using %s temp table", etl_view_name, temp_table_name)

    def update_bronze_pdr(self):
        """
        @description
            Update bronze tables
        """
        logger.info("update_bronze_pdr - Update bronze tables.")

        # st_timestamp and fin_timestamp should be valid UnixTimeMS
        st_timestamp, fin_timestamp = self._calc_bronze_start_end_ts()

        for table_name, get_data_func in self.bronze_table_getters.items():
            data = get_data_func(
                path=self.ppss.lake_ss.lake_dir,
                st_ms=st_timestamp,
                fin_ms=fin_timestamp,
            )

            logger.info("update_bronze_pdr - Inserting data into %s", table_name)
            TableRegistry().get_table(table_name)._append_to_db(
                data,
                table_type=TableType.TEMP,
            )

            # For each bronze table that we process, that data will be entered into TEMP
            # Create view so downstream queries can access production + TEMP data
            self.create_etl_view(table_name)
