from typing import Dict
import time

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.table import Table
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_table_name,
    bronze_pdr_predictions_schema,
    get_bronze_pdr_predictions_table,
)
from pdr_backend.lake.table_silver_pdr_predictions import (
    silver_pdr_predictions_table_name,
    silver_pdr_predictions_schema,
    get_silver_pdr_predictions_table,
)


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
        self.tables: Dict[str, Table] = {}

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
            self.do_silver_step()

            end_ts = time.time_ns() / 1e9
            print(f"do_etl - Completed in {end_ts - st_ts} sec.")

        except Exception as e:
            print(f"Error when executing ETL: {e}")

    def do_sync_step(self):
        """
        @description
            Call data factory to fetch data and update lake
            The sync will try 3 times to fetch from data_factory, and update the local gql_dfs
        """
        gql_tables = self.gql_data_factory.get_gql_tables()

        # rather than override the whole dict, we update the dict
        for key in gql_tables:
            self.tables[key] = gql_tables[key]

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

    def do_silver_step(self):
        """
        @description
            We have updated our bronze tables
            Now, let's build the silver tables
            key tables: [silver_pdr_predictions]
        """
        print("do_silver_step - Build silver tables.")

        # Update silver tables
        # let's keep track of time passed so we can log how long it takes for this step to complete
        st_ts = time.time_ns() / 1e9

        self.update_silver_pdr_predictions()

        end_ts = time.time_ns() / 1e9
        print(f"do_silver_step - Completed in {end_ts - st_ts} sec.")

    def update_bronze_pdr_predictions(self):
        """
        @description
            Update bronze_pdr_predictions table
        """
        if bronze_pdr_predictions_table_name not in self.tables:
            # Load existing bronze tables
            table = Table(
                bronze_pdr_predictions_table_name,
                bronze_pdr_predictions_schema,
                self.ppss,
            )
            self.tables[bronze_pdr_predictions_table_name] = table

        table = get_bronze_pdr_predictions_table(self.tables, self.ppss)
        table.save()

    def update_silver_pdr_predictions(self):
        """
        @description
            Update silver_pdr_predictions table
        """
        if silver_pdr_predictions_table_name not in self.tables:
            # Load existing silver table
            table = Table(
                silver_pdr_predictions_table_name,
                silver_pdr_predictions_schema,
                self.ppss,
            )
            self.tables[silver_pdr_predictions_table_name] = table

        table = get_silver_pdr_predictions_table(self.tables, self.ppss)
        print(table.df)
        table.save()
