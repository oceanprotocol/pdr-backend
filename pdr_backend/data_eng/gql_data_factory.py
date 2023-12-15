import os
from typing import Dict, Callable

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.timeutil import pretty_timestr, current_ut

from pdr_backend.data_eng.plutil import (
    has_data,
    newest_ut,
)

from pdr_backend.util.subgraph_predictions import (
    get_sapphire_postfix,
    get_all_contract_ids_by_owner,
)

from pdr_backend.data_eng.table_pdr_predictions import (
    predictions_schema,
    get_pdr_predictions_df,
)


@enforce_types
class GQLDataFactory:
    """
    Roles:
    - From each GQL API, fill >=1 gql_dfs -> parquet files data lake
    - From gql_dfs, calculate other dfs and stats
    - All timestamps, after fetching, are transformed into milliseconds wherever appropriate

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
       - "datetime" values ares python datetime.datetime, UTC
    """

    def __init__(self, ppss: PPSS):
        self.ppss = ppss

        # filter by feed contract address
        network = get_sapphire_postfix(ppss.web3_pp.network)
        contract_list = get_all_contract_ids_by_owner(
            owner_address=self.ppss.web3_pp.owner_addrs,
            network=network,
        )
        contract_list = [f.lower() for f in contract_list]

        # configure all tables that will be recorded onto lake
        self.record_config = {
            "pdr_predictions": {
                "fetch_fn": get_pdr_predictions_df,
                "schema": predictions_schema,
                "config": {
                    "contract_list": contract_list,
                },
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
        fin_ut = self.ppss.data_ss.fin_timestamp

        print(f"  Data start: {pretty_timestr(self.ppss.data_ss.st_timestamp)}")
        print(f"  Data fin: {pretty_timestr(fin_ut)}")

        self._update(fin_ut)
        gql_dfs = self._load_parquet(fin_ut)

        print("Get historical data across many subgraphs. Done.")

        # postconditions
        assert len(gql_dfs.values()) > 0
        for df in gql_dfs.values():
            assert isinstance(df, pl.DataFrame)

        return gql_dfs

    def _update(self, fin_ut: int):
        """
        @description
            Iterate across all gql queries and update their parquet files:
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

        for k, record in self.record_config.items():
            filename = self._parquet_filename(k)
            print(f"      filename={filename}")

            st_ut = self._calc_start_ut(filename)
            print(f"      Aim to fetch data from start time: {pretty_timestr(st_ut)}")
            if st_ut > min(current_ut(), fin_ut):
                print("      Given start time, no data to gather. Exit.")
                continue

            # to satisfy mypy, get an explicit function pointer
            do_fetch: Callable[[str, int, int, Dict], pl.DataFrame] = record["fetch_fn"]

            # call the function
            print(f"    Fetching {k}")
            df = do_fetch(self.ppss.web3_pp.network, st_ut, fin_ut, record["config"])

            # postcondition
            if len(df) > 0:
                assert df.schema == record["schema"]

                # save to parquet
                self._save_parquet(filename, df)

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
            return self.ppss.data_ss.st_timestamp

        print("      File already exists")
        if not has_data(filename):
            print("      File has no data, so delete it")
            os.remove(filename)
            return self.ppss.data_ss.st_timestamp

        file_utN = newest_ut(filename)
        return file_utN + 1000

    def _load_parquet(self, fin_ut: int) -> Dict[str, pl.DataFrame]:
        """
        @arguments
          fin_ut -- finish timestamp

        @return
          gql_dfs -- dict of [gql_filename] : df
            Where df has columns=GQL_COLS+"datetime", and index=timestamp
        """
        print("  Load parquet.")
        st_ut = self.ppss.data_ss.st_timestamp

        dfs: Dict[str, pl.DataFrame] = {}  # [parquet_filename] : df

        for k, record in self.record_config.items():
            filename = self._parquet_filename(k)
            print(f"      filename={filename}")

            # load all data from file
            df = pl.read_parquet(filename)
            df = df.filter(
                (pl.col("timestamp") >= st_ut) & (pl.col("timestamp") <= fin_ut)
            )

            # postcondition
            assert df.schema == record["schema"]
            dfs[k] = df

        return dfs

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
        filename = os.path.join(self.ppss.data_ss.parquet_dir, basename)
        return filename

    @enforce_types
    def _save_parquet(self, filename: str, df: pl.DataFrame):
        """write to parquet file
        parquet only supports appending via the pyarrow engine
        """

        # precondition
        assert "timestamp" in df.columns and df["timestamp"].dtype == pl.Int64
        assert len(df) > 0
        if len(df) > 1:
            assert (
                df.head(1)["timestamp"].to_list()[0]
                < df.tail(1)["timestamp"].to_list()[0]
            )

        if os.path.exists(filename):  # "append" existing file
            cur_df = pl.read_parquet(filename)
            df = pl.concat([cur_df, df])

            # check for duplicates and throw error if any found
            duplicate_rows = df.filter(pl.struct("id").is_duplicated())
            if len(duplicate_rows) > 0:
                raise Exception(
                    f"Not saved. Duplicate rows found. {len(duplicate_rows)} rows: {duplicate_rows}"
                )

            df.write_parquet(filename)
            n_new = df.shape[0] - cur_df.shape[0]
            print(f"  Just appended {n_new} df rows to file {filename}")
        else:  # write new file
            df.write_parquet(filename)
            print(f"  Just saved df with {df.shape[0]} rows to new file {filename}")
