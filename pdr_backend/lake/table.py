import logging
import os
from typing import Dict, Callable, Optional
import polars as pl
from polars.type_aliases import SchemaDict

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.plutil import has_data, newest_ut
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.persistent_data_store import PersistentDataStore

logger = logging.getLogger("table")


@enforce_types
class Table:
    def __init__(self, table_name: str, df_schema: SchemaDict, ppss: PPSS):
        self.ppss = ppss
        self.table_name = table_name
        self.df_schema = df_schema
        self.df = pl.DataFrame([], schema=df_schema)
        print("self.df", self.df)
        self.csv_data_store = CSVDataStore(self.ppss.lake_ss.parquet_dir)
        self.PDS = PersistentDataStore(self.ppss.lake_ss.parquet_dir)

        self.load()

    @enforce_types
    def load(self):
        """
        Read the data from the Parquet file into a DataFrame object
        """
        print(f"Loading data for {self.table_name}")

        st_ut = self.ppss.lake_ss.st_timestamp
        fin_ut = self.ppss.lake_ss.fin_timestamp
        self.df = self.csv_data_store.read(
            self.table_name, st_ut, fin_ut, schema=self.df_schema
        )

    def append_to_sources(self, data: pl.DataFrame):
        self._append_to_csv(data)
        self._append_to_db(data)

    def _append_to_csv(self, data: pl.DataFrame):
        """
        Append the data from the DataFrame object into the CSV file
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        self.csv_data_store.write(self.table_name, data, schema=self.df_schema)
        n_new = data.shape[0]
        print(
            f"  Just saved df with {n_new} df rows to the csv files of {self.table_name}"
        )

    def _append_to_db(self, data: pl.DataFrame):
        """
        Append the data from the DataFrame object into the database
        It only saves the new data that has been fetched

        @arguments:
            data - The Polars DataFrame to save.
        """
        self.PDS.insert_to_table(data, self.table_name)
        n_new = data.shape[0]
        print(
            f"  Just saved df with {n_new} df rows to the database of {self.table_name}"
        )

    def get_pds_last_record(self) -> Optional[pl.DataFrame]:
        """
        Get the last record from the persistent data store

        @returns
            pl.DataFrame
        """

        query = "SELECT * FROM {view_name} ORDER BY timestamp DESC LIMIT 1"
        try:
            return self.PDS.query_data(self.table_name, query)
        except Exception as e:
            print(f"Error fetching last record from PDS: {e}")
            return None

    @enforce_types
    def get_pdr_df(
        self,
        fetch_function: Callable,
        network: str,
        st_ut: UnixTimeMs,
        fin_ut: UnixTimeMs,
        save_backoff_limit: int,
        pagination_limit: int,
        config: Dict,
    ):
        """
        @description
            Fetch raw data from predictoor subgraph
            Update function for graphql query, returns raw data
            + Transforms ts into ms as required for data factory
        """
        print(f"Fetching data for {self.table_name}")
        network = get_sapphire_postfix(network)

        # save to file when this amount of data is fetched
        save_backoff_count = 0
        pagination_offset = 0

        final_df = pl.DataFrame([], schema=self.df_schema)

        while True:
            # call the function
            data = fetch_function(
                st_ut.to_seconds(),
                fin_ut.to_seconds(),
                config["contract_list"],
                pagination_limit,
                pagination_offset,
                network,
            )

            print(f"Fetched {len(data)} from subgraph")
            # convert predictions to df and transform timestamp into ms
            df = _object_list_to_df(data, self.df_schema)
            df = _transform_timestamp_to_ms(df)
            df = df.filter(pl.col("timestamp").is_between(st_ut, fin_ut)).sort(
                "timestamp"
            )

            if len(final_df) == 0:
                final_df = df
            else:
                final_df = final_df.vstack(df)

            save_backoff_count += len(df)

            # save to file if requred number of data has been fetched
            if (
                save_backoff_count >= save_backoff_limit or len(df) < pagination_limit
            ) and len(final_df) > 0:
                assert df.schema == self.df_schema
                # save to parquet
                self.append_to_sources(final_df)

                print(f"Saved {len(final_df)} records to file while fetching")
                final_df = pl.DataFrame([], schema=self.df_schema)
                save_backoff_count = 0

            # avoids doing next fetch if we've reached the end
            if len(df) < pagination_limit:
                break
            pagination_offset += pagination_limit

        if len(final_df) > 0:
            self.append_to_sources(final_df)

            print(f"Saved {len(final_df)} records to file while fetching")
