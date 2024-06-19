import logging
import time
from typing import Dict, List, Optional, Tuple

from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.gql_data_factory import (
    GQLDataFactory,
    _GQLDF_REGISTERED_TABLE_NAMES,
)
from pdr_backend.lake.table import ETLTable, NamedTable, TempTable
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("etl")


# Registered ETL queries & tables
_ETL_REGISTERED_LAKE_TABLES = [BronzePrediction]

_ETL_REGISTERED_TABLE_NAMES = [
    t.get_lake_table_name() for t in _ETL_REGISTERED_LAKE_TABLES
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
            db.drop_view(ETLTable(table_name).fullname)
            db.drop_table(TempTable(table_name).fullname)

    def _move_from_temp_tables_to_live(self):
        """
        @description
            Move the records from our bronze temporary tables to live, in-production tables
        """

        db = DuckDBDataStore(self.ppss.lake_ss.lake_dir)
        for dataclass in _ETL_REGISTERED_LAKE_TABLES:
            table_name = dataclass.get_lake_table_name()
            logger.info("move table %s to live", table_name)
            temp_table = TempTable(table_name)
            permanent_table = NamedTable(table_name)

            if db.table_exists(temp_table.fullname):
                db.move_table_data(temp_table, permanent_table)

                db.drop_view(ETLTable(table_name).fullname)
                db.drop_table(temp_table.fullname)

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
            self.gql_data_factory._update()
            logger.info("do_etl - Synced data. Start bronze_step.")

            self.do_bronze_step()

            end_ts = time.time_ns() / 1e9
            logger.info("do_etl - Completed bronze_step in %s sec.", end_ts - st_ts)

            # Move data to live at end of ETL
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
            key tables: [bronze_pdr_predictions]
        """
        logger.info("do_bronze_step - Build bronze tables.")

        # Update bronze tables
        # let's keep track of time passed so we can log how long it takes for this step to complete
        st_ts = time.time_ns() / 1e9

        self.update_bronze_pdr()

        end_ts = time.time_ns() / 1e9
        logger.info("do_bronze_step - Completed in %s sec.", end_ts - st_ts)

    @enforce_types
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

        all_db_tables = DuckDBDataStore(self.ppss.lake_ss.lake_dir).get_table_names()

        queries = []

        for table in tables:
            if table.fullname not in all_db_tables:
                logger.info(
                    "_get_max_timestamp_values_from - Table %s does not exist.",
                    table.fullname,
                )
                continue

            queries.append(max_timestamp_query.format(table.fullname, table.fullname))

        logger.info("_get_max_timestamp_values_from - queries: %s", queries)

        table_names = [table.fullname for table in tables]
        none_values: Dict[str, Optional[UnixTimeMs]] = {
            table_name: None for table_name in table_names
        }

        if len(queries) == 0:
            return none_values

        final_query = " UNION ALL ".join(queries)
        result = DuckDBDataStore(self.ppss.lake_ss.lake_dir).query_data(final_query)

        logger.info("_get_max_timestamp_values_from - result: %s", result)

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
            [NamedTable(tb) for tb in table_names]
        )

        logger.info(
            "get_timestamp_values - max_timestamp_values: %s", max_timestamp_values
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

        logger.info("get_timestamp_values - values: %s", values)
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
        """
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

    @enforce_types
    def create_etl_view(self, table_name: str):
        # Assemble view query and create the view
        assert (
            table_name in _ETL_REGISTERED_TABLE_NAMES
        ), f"{table_name} must be a bronze table"

        db = DuckDBDataStore(self.ppss.lake_ss.lake_dir)
        temp_table = TempTable(table_name)
        etl_view = ETLTable(table_name)

        table_exists = db.table_exists(table_name)
        temp_table_exists = db.table_exists(temp_table.fullname)
        etl_view_exists = db.view_exists(etl_view.fullname)
        assert temp_table_exists, f"{temp_table.fullname} must already exist"
        if etl_view_exists:
            logger.error("%s must not exist", etl_view.fullname)
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
                etl_view.fullname,
                table_name,
                temp_table.fullname,
            )
            db.query_data(view_query)
            logger.info(
                "  Created %s view using %s table and %s temp table",
                etl_view.fullname,
                table_name,
                temp_table.fullname,
            )
        else:
            view_query = f"CREATE VIEW {etl_view.fullname} AS SELECT * FROM {temp_table.fullname}"
            db.query_data(view_query)
            logger.info(
                "  Created %s view using %s temp table",
                etl_view.fullname,
                temp_table.fullname,
            )

    def update_bronze_pdr(self):
        """
        @description
            Update bronze tables
        """
        logger.info("update_bronze_pdr - Update bronze tables.")

        # st_timestamp and fin_timestamp should be valid UnixTimeMS
        st_timestamp, fin_timestamp = self._calc_bronze_start_end_ts()

        for dataclass in _ETL_REGISTERED_LAKE_TABLES:
            etl_func = dataclass.get_fetch_function()
            etl_func(
                path=self.ppss.lake_ss.lake_dir,
                st_ms=st_timestamp,
                fin_ms=fin_timestamp,
            )

            logger.info(
                "update_bronze_pdr - Inserting data into %s",
                dataclass.get_lake_table_name(),
            )

            # For each bronze table that we process, that data will be entered into TEMP
            # Create view so downstream queries can access production + TEMP data
            self.create_etl_view(dataclass.get_lake_table_name())
