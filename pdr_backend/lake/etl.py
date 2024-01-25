from typing import Dict
import os
import polars as pl

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.bronze_table_pdr_predictions import (
    bronze_pdr_predictions_table_name,
    bronze_pdr_predictions_schema,
    get_bronze_pdr_predictions_df,
)


class ETL:
    def __init__(self, ppss: PPSS, gql_data_factory: GQLDataFactory):
        self.ppss = ppss

        self.gql_data_factory = gql_data_factory
        self.dfs: Dict[str, pl.DataFrame] = {}

    def do_sync_step(self):
        """
        @description
            Call data factory to fetch data and update lake
            The sync will try 3 times to fetch from data_factory, and update the local gql_dfs
        """
        _retries = 3
        for i in range(_retries):
            try:
                gql_dfs = self.gql_data_factory.get_gql_dfs()

                # rather than override the whole dict, we update the dict
                for key in gql_dfs:
                    self.dfs[key] = gql_dfs[key]

                print("Fetch data from data_factory successfully")
                break
            except Exception as e:
                print(f"Error when syncing data_factory: {e}")
                print(f"Retrying {_retries - i} times")
                continue

    def do_bronze_step(self):
        """
        @description
            We have updated our lake's raw data
            Now,, let's build the bronze tables
            key tables: [bronze_pdr_predictions and bronze_pdr_slots]
        """
        # Load existing bronze tables
        filename = self.gql_data_factory._parquet_filename(
            bronze_pdr_predictions_table_name
        )
        if os.path.exists(filename):
            df = pl.read_parquet(filename)
        else:
            df = pl.DataFrame(schema=bronze_pdr_predictions_schema)

        self.dfs[bronze_pdr_predictions_table_name] = df

        # Update bronze tables
        self.update_bronze_pdr_predictions()

    def update_bronze_pdr_predictions(self):
        """
        @description
            Update bronze_pdr_predictions table
        """
        df = get_bronze_pdr_predictions_df(self.dfs, self.ppss)

        filename = self.gql_data_factory._parquet_filename(
            bronze_pdr_predictions_table_name
        )
        self.gql_data_factory._save_parquet(filename, df)

        self.dfs[bronze_pdr_predictions_table_name] = df
