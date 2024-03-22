import logging
import os
from typing import Dict, Callable
import polars as pl
from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.plutil import has_data, newest_ut
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.lake.table_pdr_subscriptions import subscriptions_table_name
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms

logger = logging.getLogger("table")


@enforce_types
class Table:
    def __init__(self, table_name: str, df_schema: object, ppss: PPSS):
        self.ppss = ppss
        self.table_name = table_name
        self.df_schema = df_schema
        self.df = pl.DataFrame()
        self.load()

    @enforce_types
    def load(self):
        """
        Read the data from the Parquet file into a DataFrame object
        """
        filename = self._parquet_filename()

        # set simestamp for subscriptions 1 day earlier
        st_ut = (
            (self.ppss.lake_ss.st_timestamp - 86400000)
            if (self.table_name == subscriptions_table_name)
            else self.ppss.lake_ss.st_timestamp
        )

        fin_ut = self.ppss.lake_ss.fin_timestamp

        # load all data from file
        # check if file exists
        # if file doesn't exist, return an empty dataframe with the expected schema
        if os.path.exists(filename):
            logger.info("Loading parquet for %s", self.table_name)
            df = pl.read_parquet(filename)
            df = df.filter(
                (pl.col("timestamp") >= st_ut) & (pl.col("timestamp") <= fin_ut)
            )
        else:
            logger.info("Create initial df for %s", self.table_name)
            df = pl.DataFrame(schema=self.df_schema)

        # save data frame in memory
        self.df = df

    @enforce_types
    def save(self):
        """
        Get the data from subgraph and write it to Parquet file
        write to parquet file
        parquet only supports appending via the pyarrow engine
        """

        assert "timestamp" in self.df.columns and self.df["timestamp"].dtype == pl.Int64
        assert len(self.df) > 0
        if len(self.df) > 2:
            assert (
                self.df.head(1)["timestamp"].to_list()[0]
                <= self.df.tail(1)["timestamp"].to_list()[0]
            )

        filename = self._parquet_filename()
        if os.path.exists(filename):  # "append" existing file
            cur_df = pl.read_parquet(filename)
            cur_df_ID_columns = cur_df["ID"].to_list()

            # drop duplicates
            self.df = self.df.filter(pl.col("ID").is_in(cur_df_ID_columns).not_())
            self.df = pl.concat([cur_df, self.df])
            self.df.write_parquet(filename)
            n_new = self.df.shape[0] - cur_df.shape[0]
            print(f"  Just appended {n_new} df rows to file {filename}")
        else:  # write new file
            self.df.write_parquet(filename)
            print(
                f"  Just saved df with {self.df.shape[0]} rows to new file {filename}"
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
        network = get_sapphire_postfix(network)

        # save to file when this amount of data is fetched
        save_backoff_count = 0
        pagination_offset = 0

        final_df = pl.DataFrame()

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

            print(f"Fetched {len(data)} from subgraph for {self.table_name}")
            # convert predictions to df and transform timestamp into ms
            df = _object_list_to_df(data, self.df_schema)
            df = _transform_timestamp_to_ms(df)
            df = df.filter(pl.col("timestamp").is_between(st_ut, fin_ut)).sort(
                "timestamp"
            )
            if len(final_df) == 0:
                final_df = df
            else:
                final_df = pl.concat([final_df, df])

            save_backoff_count += len(df)

            # save to file if requred number of data has been fetched
            if (
                save_backoff_count >= save_backoff_limit or len(df) < pagination_limit
            ) and len(final_df) > 0:
                assert df.schema == self.df_schema
                # save to parquet
                self.df = final_df.select(df.schema)
                self.save()
                print(f"Saved {len(final_df)} records to file while fetching")
                final_df = pl.DataFrame()
                save_backoff_count = 0

            # avoids doing next fetch if we've reached the end
            if len(df) < pagination_limit:
                break
            pagination_offset += pagination_limit

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
