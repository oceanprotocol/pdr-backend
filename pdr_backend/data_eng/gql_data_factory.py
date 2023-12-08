import os
from typing import Dict, List

from enforce_typing import enforce_types
import polars as pl
from polars import Utf8, Int64, Float64, Boolean

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.timeutil import pretty_timestr, current_ut, ms_to_seconds

from pdr_backend.data_eng.plutil import (
    has_data,
    oldest_ut_ms,
    newest_ut_ms,
)

from pdr_backend.util.subgraph_predictions import (
    fetch_filtered_predictions,
    FilterMode,
)


# RAW_PREDICTIONS_SCHEMA
predictions_schema = {
    "id": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "prediction": Boolean,
    "stake": Float64,
    "trueval": Boolean,
    "timestamp": Int64,
    "source": Utf8,
    "payout": Float64,
    "slot": Int64,
    "user": Utf8,
}


# TO DO: abstract sync operations => factory_config["update_fn"]()
# mypy: disable-error-code=operator
@enforce_types
class GQLDataFactory:
    """
    Roles:
    - From each GQL API, fill >=1 parquet_dfs -> parquet files data lake
    - From parquet_dfs, calculate stats and other dfs
    - GQLDataFactory expects "timestamp_ms" column to be injected into all raw dfs

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
       - "datetime" values ares python datetime.datetime, UTC
    """

    def __init__(self, pp: DataPP, ss: DataSS, web3: Web3PP):
        self.pp = pp
        self.ss = ss
        self.web3 = web3

        # TO-DO: Roll into yaml config
        self.factory_config = {
            "raw_predictions": {
                "update_fn": self._update_hist_predictions,
                "schema": predictions_schema,
            },
        }

    def get_gql_dfs(self) -> Dict[str, pl.DataFrame]:
        """
        @description
          Get historical dataframes across many feeds and timeframes.

        @return
          predictions_df -- *polars* Dataframe. See class docstring
        """
        print("Get predictions data across many feeds and timeframes.")

        # Ss_timestamp is calculated dynamically if ss.fin_timestr = "now".
        # But, we don't want fin_timestamp changing as we gather data here.
        # To solve, for a given call to this method, we make a constant fin_ut
        fin_ut = self.ss.fin_timestamp

        print(f"  Data start: {pretty_timestr(self.ss.st_timestamp)}")
        print(f"  Data fin: {pretty_timestr(fin_ut)}")

        self._update_parquet(fin_ut)
        gql_dfs = self._load_parquet(fin_ut)

        print("Get historical data across many subgraphs. Done.")

        # postconditions
        assert len(gql_dfs.values()) > 0
        for df in gql_dfs.values():
            assert isinstance(df, pl.DataFrame)

        return gql_dfs

    def _update_parquet(self, fin_ut: int):
        print("  Update parquet.")
        self._update_hist_parquet(fin_ut)

    def _update_hist_parquet(self, fin_ut: int):
        """
        @description
            Update raw data for:
            - Predictoors
            - Slots
            - Claims

            Improve this by:
            1. Break out raw data from any transformed/cleaned data
            2. Integrate other queries and summaries
            3. Integrate config/pp if needed
        @arguments
            fin_ut -- a timestamp, in ms, in UTC
        """

        for k, config in self.factory_config.items():
            filename = self._parquet_filename(k)
            print(f"      filename={filename}")

            st_ut = self._calc_start_ut(filename)
            print(f"      Aim to fetch data from start time: {pretty_timestr(st_ut)}")
            if st_ut > min(current_ut(), fin_ut):
                print("      Given start time, no data to gather. Exit.")
                continue

            print(f"    Fetching {k}")
            config["update_fn"](st_ut, fin_ut, filename, config)

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
            return self.ss.st_timestamp

        print("      File already exists")
        if not has_data(filename):
            print("      File has no data, so delete it")
            os.remove(filename)
            return self.ss.st_timestamp

        # gql data is in seconds, not ms
        file_ut0, file_utN = oldest_ut_ms(filename), newest_ut_ms(filename)
        print(f"      Oldest record: {pretty_timestr(file_ut0)}")
        print(f"      Latest record: {pretty_timestr(file_utN)}")
        print(f"      Resume from latest + 1 sec: {pretty_timestr(file_utN + 1000)}")
        return file_utN + 1000

    def _load_parquet(self, fin_ut: int) -> Dict[str, pl.DataFrame]:
        """
        @arguments
          fin_ut -- finish timestamp

        @return
          parquet_dfs -- dict of [parquet_filename] : df
            Where df has columns=GQL_COLS+"datetime", and index=timestamp
        """
        print("  Load parquet.")
        st_ut = self.ss.st_timestamp

        gql_dfs: Dict[str, pl.DataFrame] = {}  # [parquet_filename] : df

        for k, config in self.factory_config.items():
            filename = self._parquet_filename(k)
            print(f"      filename={filename}")

            # load all data from file
            parquet_df = pl.read_parquet(filename)
            parquet_df = parquet_df.filter(
                (pl.col("timestamp_ms") >= st_ut) & (pl.col("timestamp_ms") <= fin_ut)
            )

            # postcondition
            assert (
                "timestamp" in parquet_df.columns
                and parquet_df["timestamp"].dtype == pl.Int64
            )
            assert (
                "timestamp_ms" in parquet_df.columns
                and parquet_df["timestamp_ms"].dtype == pl.Int64
            )

            # timestmap_ms should be the only extra column
            assert parquet_df.drop("timestamp_ms").schema == config["schema"]

            gql_dfs[k] = parquet_df

        return gql_dfs

    def _parquet_filename(self, filename_str: str) -> str:
        """
        @description
          Computes the lake-path for the parquet file.

        @arguments
          filename_str -- eg "subgraph_predictions"

        @return
          parquet_filename -- name for parquet file.
        """
        gql_dir = os.path.join(self.ss.parquet_dir, "gql")
        if not os.path.exists(gql_dir):
            os.makedirs(gql_dir)

        basename = f"{filename_str}.parquet"
        filename = os.path.join(gql_dir, basename)
        return filename

    def _transform_timestamp(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.with_columns(
            [
                pl.col("timestamp").mul(1000).alias("timestamp_ms"),
            ]
        )
        return df

    def _update_hist_predictions(
        self, st_ut: int, fin_ut: int, filename: str, config: Dict
    ):
        """
        @description
            Fetch raw predictions from subgraph, and save to parquet file.

            Update function for graphql query, returns raw data + timestamp_ms
            such that the rest of gql_data_factory can work with ms
        """
        # get network
        if "main" in self.web3.network:
            network = "mainnet"
        elif "test" in self.web3.network:
            network = "testnet"
        else:
            raise ValueError(self.web3.network)

        # fetch predictions
        predictions = fetch_filtered_predictions(
            ms_to_seconds(st_ut),
            ms_to_seconds(fin_ut),
            [],
            network,
            FilterMode.NONE,
            payout_only=False,
            trueval_only=False,
        )

        if len(predictions) == 0:
            print("      No predictions to fetch. Exit.")
            return

        # convert predictions to df and calculate timestamp_ms
        predictions_df = self._object_list_to_df(predictions, config["schema"])
        predictions_df = self._transform_timestamp(predictions_df)

        # output to parquet
        self._save_parquet(filename, predictions_df)

    def _object_list_to_df(self, objects: List[object], schema: Dict) -> pl.DataFrame:
        """
        @description
            Convert list objects to a dataframe using their __dict__ structure.
        """
        # Get all predictions into a dataframe
        obj_dicts = [object.__dict__ for object in objects]
        obj_df = pl.DataFrame(obj_dicts, schema=schema)
        assert obj_df.schema == schema

        return obj_df

    @enforce_types
    def _save_parquet(self, filename: str, df: pl.DataFrame):
        """write to parquet file
        parquet only supports appending via the pyarrow engine
        """

        # precondition
        assert "timestamp" in df.columns and df["timestamp"].dtype == pl.Int64
        assert "timestamp_ms" in df.columns and df["timestamp_ms"].dtype == pl.Int64

        if os.path.exists(filename):  # append existing file
            # TO DO: Implement parquet-append with pyarrow
            cur_df = pl.read_parquet(filename)
            df = pl.concat([cur_df, df])
            df.write_parquet(filename)
            n_new = df.shape[0] - cur_df.shape[0]
            print(f"  Just appended {n_new} df rows to file {filename}")
        else:  # write new file
            df.write_parquet(filename)
            print(f"  Just saved df with {df.shape[0]} rows to new file {filename}")
