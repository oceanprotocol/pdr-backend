import os
from typing import Callable
import polars as pl
from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.plutil import has_data, newest_ut
from pdr_backend.util.timeutil import current_ut_ms, pretty_timestr


@enforce_types
class Table:
    def __init__(self, table_name: str, df_schema: object, build_df_fn, ppss: PPSS):
        self.ppss = ppss
        self.table_name = table_name
        self.df_schema = df_schema
        self.build = build_df_fn
        self.df = pl.DataFrame()
        self.load()

    @enforce_types
    def load(self):
        """
        Read the data from the Parquet file into a DataFrame object
        """
        filename = self._parquet_filename(self.table_name)
        print(f"      filename={filename}")
        st_ut = self.ppss.lake_ss.st_timestamp
        fin_ut = self.ppss.lake_ss.fin_timestamp

        # load all data from file
        # check if file exists
        # if file doesn't exist, return an empty dataframe with the expected schema
        if os.path.exists(filename):
            df = pl.read_parquet(filename)
        else:
            print("file doesn't exist")
            df = pl.DataFrame(schema=self.df_schema)

        df = df.filter((pl.col("timestamp") >= st_ut) & (pl.col("timestamp") <= fin_ut))

        # save data frame in memory
        print(df)
        self.df = df

    @enforce_types
    def save(self):
        """
        Get the data from subgraph and write it to Parquet file
        write to parquet file
        parquet only supports appending via the pyarrow engine
        """

        print(self.df)
        # precondition
        assert "timestamp" in self.df.columns and self.df["timestamp"].dtype == pl.Int64
        assert len(self.df) > 0
        if len(self.df) > 1:
            assert (
                self.df.head(1)["timestamp"].to_list()[0]
                <= self.df.tail(1)["timestamp"].to_list()[0]
            )

        filename = self._parquet_filename(self.table_name)

        if os.path.exists(filename):  # "append" existing file
            cur_df = pl.read_parquet(filename)
            self.df = pl.concat([cur_df, self.df])

            # drop duplicates
            self.df = self.df.filter(pl.struct("ID").is_unique())
            self.df.write_parquet(filename)
            n_new = self.df.shape[0] - cur_df.shape[0]
            print(f"  Just appended {n_new} df rows to file {filename}")
        else:  # write new file
            self.df.write_parquet(filename)
            print(
                f"  Just saved df with {self.df.shape[0]} rows to new file {filename}"
            )

    @enforce_types
    def update(self, config: object):
        """
        Get the data from subgraph and write it to Parquet file
        """
        filename = self._parquet_filename(self.table_name)
        st_ut = self._calc_start_ut(filename)
        fin_ut = self.ppss.lake_ss.fin_timestamp
        print(f"      Aim to fetch data from start time: {pretty_timestr(st_ut)}")
        if st_ut > min(current_ut_ms(), fin_ut):
            print("      Given start time, no data to gather. Exit.")

        # to satisfy mypy, get an explicit function pointer
        do_fetch: Callable[[str, int, int, object], pl.DataFrame] = self.build

        # call the function
        print(f"    Fetching {self.table_name}")
        df = do_fetch(self.ppss.web3_pp.network, st_ut, fin_ut, config)

        # postcondition
        if len(df) > 0:
            assert df.schema == self.df_schema

        self.df = df
        # save to parquet
        if len(df) > 0:
            self.save()

    @enforce_types
    def _parquet_filename(self, filename_str: str) -> str:
        """
        @description
          Computes the lake-path for the parquet file.

        @arguments
          filename_str -- eg "subgraph_predictions"

        @return
          parquet_filename -- name for parquet file.
        """
        basename = f"{filename_str}.parquet"
        filename = os.path.join(self.ppss.lake_ss.parquet_dir, basename)
        return filename

    @enforce_types
    def _calc_start_ut(self, filename: str) -> int:
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
        return file_utN + 1000
