import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from pdr_backend.ppss.ppss import PPSS
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
from pdr_backend.lake.plutil import get_table_name, TableType
from pdr_backend.util.time_types import UnixTimeMs


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
            subscriptions_table_name,
            truevals_table_name,
            slots_table_name
        ]

        self.bronze_table_getters = {
            bronze_pdr_predictions_table_name: get_bronze_pdr_predictions_data_with_SQL,
            bronze_pdr_slots_table_name: get_bronze_pdr_slots_data_with_SQL,
        }

        self.bronze_table_names = list(self.bronze_table_getters.keys())

        self.temp_table_names = [*self.bronze_table_names, *self.raw_table_names]

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
            pds.move_table_data(
                get_table_name(table_name, TableType.TEMP),
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
        print("do_etl - Start ETL.")

        try:
            # Drop any build tables if they already exist
            self._drop_temp_sql_tables()
            print("do_etl - Drop build tables.")

            # Sync data
            self.gql_data_factory.get_gql_tables()
            print("do_etl - Synced data. Start bronze_step.")

            self.do_bronze_step()

            end_ts = time.time_ns() / 1e9
            print(f"do_etl - Completed bronze_step in {end_ts - st_ts} sec.")

            self._move_from_temp_tables_to_live()
            print("do_etl - Moved build tables to permanent tables. ETL Complete.")
        except Exception as e:
            print(f"Error when executing ETL: {e}")

    def do_bronze_step(self):
        """
        @description
            We have updated our lake's raw data
            Now, let's build the bronze tables
            key tables: [bronze_pdr_predictions and bronze_pdr_slots]
        """
        print("do_bronze_step - Build bronze tables.")

        # Update bronze tables
        # let's keep track of time passed so we can log how long it takes for this step to complete
        st_ts = time.time_ns() / 1e9

        self.update_bronze_pdr()

        end_ts = time.time_ns() / 1e9
        print(f"do_bronze_step - Completed in {end_ts - st_ts} sec.")

    def _get_max_timestamp_values_from(
        self, table_names: List[str], table_type: TableType = TableType.NORMAL
    ) -> Dict[str, Optional[datetime]]:
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

        queries = [
            max_timestamp_query.format(
                get_table_name(table_name, table_type),
                get_table_name(table_name, table_type),
            )
            for table_name in table_names
        ]
        final_query = " UNION ALL ".join(queries)

        print(f"_get_max_timestamp_values_from - final_query: {final_query}")

        result = PersistentDataStore(self.ppss.lake_ss.lake_dir).query_data(final_query)

        print(f"_get_max_timestamp_values_from - result: {result}")
        values: Any = {}

        if result is None:
            for table_name in table_names:
                values[table_name] = None

            return values

        # print(f"_get_max_timestamp_values_from - result: {result}")

        for row in result.rows(named=True):
            table_name = row["table_name"]
            max_timestamp = row["max_timestamp"]
            values[table_name] = max_timestamp

        return values

    def _calc_bronze_start_end_ts(self):
        """
        @description
            Calculate the start and end timestamps for the bronze tables
            ETL updates should use from_timestamp by calculating
            max(etl_tables_max_timestamp).
            ETL updates should use to_timestamp by calculating
            min(max(source_tables_max_timestamp)).
        """
        from_values = self._get_max_timestamp_values_from(
            self.bronze_table_names
        ).values()

        from_timestamp = (
            min(from_values)
            if None not in from_values
            else datetime.strptime(self.ppss.lake_ss.st_timestr, "%Y-%m-%d_%H:%M")
        )

        to_values = self._get_max_timestamp_values_from(
            self.raw_table_names, TableType.TEMP
        ).values()

        to_timestamp = (
            min(to_values)
            if None not in to_values
            else datetime.strptime(self.ppss.lake_ss.fin_timestr, "%Y-%m-%d_%H:%M")
        )

        return from_timestamp, to_timestamp

    def update_bronze_pdr(self):
        """
        @description
            Update bronze tables
        """
        print("update_bronze_pdr - Update bronze tables.")
        st_timestamp, fin_timestamp = self._calc_bronze_start_end_ts()

        for table_name, get_data_func in self.bronze_table_getters.items():
            # If st_timestamp is an instance of datetime, convert it to UnixTimeMs with from_dt
            # If st_timestamp is None, it will be passed as None
            # If st_timestamp is an int, Convert it to UnixTimeMs by passing it as is
            st_ms = UnixTimeMs.from_dt(st_timestamp) if isinstance(
                st_timestamp, datetime) else UnixTimeMs(st_timestamp)
            fin_ms = UnixTimeMs.from_dt(fin_timestamp) if isinstance(
                fin_timestamp, datetime) else UnixTimeMs(fin_timestamp)

            data = get_data_func(
                path=self.ppss.lake_ss.lake_dir,
                st_ms=st_ms,
                fin_ms=fin_ms
            )

            TableRegistry().get_table(table_name)._append_to_db(
                data,
                table_type=TableType.TEMP,
            )
