import logging
import os
from typing import Dict, Callable
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
        self.load()

    @enforce_types
    def load(self):
        """
        Read the data from the Parquet file into a DataFrame object
        """
        print(f"Loading data for {self.table_name}")
        self.csv_data_store = CSVDataStore(self.ppss.lake_ss.parquet_dir)
        self.persistent_data_store = PersistentDataStore(self.ppss.lake_ss.parquet_dir)

        st_ut = self.ppss.lake_ss.st_timestamp
        fin_ut = self.ppss.lake_ss.fin_timestamp
        self.df = self.csv_data_store.read(
            self.table_name, st_ut, fin_ut, schema=self.df_schema
        )

    def append_to_storage(self, data: pl.DataFrame):
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
        self.persistent_data_store.insert_to_table(data, self.table_name)
        n_new = data.shape[0]
        print(
            f"  Just saved df with {n_new} df rows to the database of {self.table_name}"
        )

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

        buffer_df = pl.DataFrame([], schema=self.df_schema)

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

            if len(buffer_df) == 0:
                buffer_df = df
            else:
                buffer_df = buffer_df.vstack(df)

            save_backoff_count += len(df)

            # save to file if requred number of data has been fetched
            if (
                save_backoff_count >= save_backoff_limit or len(df) < pagination_limit
            ) and len(buffer_df) > 0:
                assert df.schema == self.df_schema
                self.append_to_storage(buffer_df)

                print(f"Saved {len(buffer_df)} records to file while fetching")
                buffer_df = pl.DataFrame([], schema=self.df_schema)
                save_backoff_count = 0

            # avoids doing next fetch if we've reached the end
            if len(df) < pagination_limit:
                break
            pagination_offset += pagination_limit

        if len(buffer_df) > 0:
            self.append_to_storage(buffer_df)
            print(f"Saved {len(buffer_df)} records to file while fetching")

    @enforce_types
    def _parquet_filename(self) -> str:
        """
        @description
            Computes the lake-path for the parquet file.

        @arguments
            filename_str -- eg "subgraph_predictions"

        @return
            parquet_filename -- name for parquet file.
        """
        basename = f"{self.table_name}.parquet"
        filename = os.path.join(self.ppss.lake_ss.parquet_dir, basename)
        return filename

    @enforce_types
    def _calc_start_ut(self, filename: str) -> UnixTimeMs:
        """
        @description
            Calculate start timestamp, reconciling whether file exists and where
            its data starts. If file exists, you can only append to end.

        @arguments
        filename - parquet file with data. May or may not exist.

        @return
        start_ut - timestamp (ut) to start grabbing data for (in ms)
        """
        if not os.path.exists(filename):
            print("      No file exists yet, so will fetch all data")
            return self.ppss.lake_ss.st_timestamp

        print("      File already exists")
        if not has_data(filename):
            print("      File has no data, so delete it")
            os.remove(filename)
            return self.ppss.lake_ss.st_timestamp

        file_utN = newest_ut(filename)
        return UnixTimeMs(file_utN + 1000)
