import time

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_table_name,
    bronze_pdr_predictions_schema,
    get_bronze_pdr_predictions_data_with_SQL,
)
from pdr_backend.lake.table_registry import TableRegistry


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

    def do_etl(self):
        """
        @description
            Run the ETL process
        """

        st_ts = time.time_ns() / 1e9
        print("do_etl - Start ETL.")

        try:
            self.do_sync_step()
            self.do_bronze_step()

            end_ts = time.time_ns() / 1e9
            print(f"do_etl - Completed in {end_ts - st_ts} sec.")

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

        self.update_bronze_pdr_predictions()

        end_ts = time.time_ns() / 1e9
        print(f"do_bronze_step - Completed in {end_ts - st_ts} sec.")

    def update_bronze_pdr_predictions(self):
        """
        @description
            Update bronze_pdr_predictions table
        """
        print("update_bronze_pdr_predictions - Update bronze_pdr_predictions table.")
        table = TableRegistry().register_table(
            bronze_pdr_predictions_table_name,
            (
                bronze_pdr_predictions_table_name,
                bronze_pdr_predictions_schema,
                self.ppss,
            ),
        )

        data = get_bronze_pdr_predictions_data_with_SQL(self.ppss)
        table.append_to_storage(data)
