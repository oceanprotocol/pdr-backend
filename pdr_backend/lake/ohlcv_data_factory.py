import os
from typing import Dict, List, Union

from enforce_typing import enforce_types
import numpy as np
import polars as pl

from pdr_backend.lake.constants import (
    OHLCV_MULT_MIN,
    OHLCV_MULT_MAX,
    TOHLCV_SCHEMA_PL,
)
from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv
from pdr_backend.lake.plutil import (
    initialize_rawohlcv_df,
    transform_df,
    concat_next_df,
    load_rawohlcv_file,
    save_rawohlcv_file,
    has_data,
    oldest_ut,
    newest_ut,
)
from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.util.timeutil import pretty_timestr, current_ut


@enforce_types
class OhlcvDataFactory:
    """
    Roles:
    - From each CEX API, fill >=1 rawohlcv_dfs -> rawohlcv files data lake
    - From rawohlcv_dfs, fill 1 mergedohlcv_df -- all data across all CEXes

    Where:
      rawohlcv_dfs -- dict of [exch_str][pair_str] : df
        And df has columns of: "open", "high", .., "volume", "datetime"
        Where pair_str must have '/' not '-', to avoid key issues
        (and index = timestamp)

      mergedohlcv_df -- polars DataFrame with cols like:
        "timestamp",
        "binanceus:ETH-USDT:open",
        "binanceus:ETH-USDT:high",
        "binanceus:ETH-USDT:low",
        "binanceus:ETH-USDT:close",
        "binanceus:ETH-USDT:volume",
        ...
        "datetime",
        (and no index)

      #For each column: oldest first, newest at the end

    And:
      X -- 2d array of [sample_i, var_i] : value -- inputs for model
      y -- 1d array of [sample_i] -- target outputs for model

      x_df -- *pandas* DataFrame with cols like:
        "binanceus:ETH-USDT:open:t-3",
        "binanceus:ETH-USDT:open:t-2",
        "binanceus:ETH-USDT:open:t-1",
        "binanceus:ETH-USDT:high:t-3",
        "binanceus:ETH-USDT:high:t-2",
        "binanceus:ETH-USDT:high:t-1",
        ...
        "datetime",
        (and index = 0, 1, .. -- nothing special)

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
       - "datetime" values ares python datetime.datetime, UTC
    """

    def __init__(self, pp: DataPP, ss: DataSS):
        self.pp = pp
        self.ss = ss

    def get_mergedohlcv_df(self) -> pl.DataFrame:
        """
        @description
          Get dataframe of all ohlcv data: merged from many exchanges & pairs.

        @return
          mergedohlcv_df -- *polars* Dataframe. See class docstring
        """
        print("Get historical data, across many exchanges & pairs: begin.")

        # Ss_timestamp is calculated dynamically if ss.fin_timestr = "now".
        # But, we don't want fin_timestamp changing as we gather data here.
        # To solve, for a given call to this method, we make a constant fin_ut
        fin_ut = self.ss.fin_timestamp

        print(f"  Data start: {pretty_timestr(self.ss.st_timestamp)}")
        print(f"  Data fin: {pretty_timestr(fin_ut)}")

        self._update_rawohlcv_files(fin_ut)
        rawohlcv_dfs = self._load_rawohlcv_files(fin_ut)
        mergedohlcv_df = _merge_rawohlcv_dfs(rawohlcv_dfs)

        print("Get historical data, across many exchanges & pairs: done.")

        # postconditions
        assert isinstance(mergedohlcv_df, pl.DataFrame)
        return mergedohlcv_df

    def _update_rawohlcv_files(self, fin_ut: int):
        print("  Update all rawohlcv files: begin")
        for exch_str, pair_str in self.ss.exchange_pair_tups:
            self._update_rawohlcv_files_at_exch_and_pair(exch_str, pair_str, fin_ut)
        print("  Update all rawohlcv files: done")

    def _update_rawohlcv_files_at_exch_and_pair(
        self, exch_str: str, pair_str: str, fin_ut: int
    ):
        """
        @arguments
          exch_str -- eg "binanceus"
          pair_str -- eg "BTC/USDT". Not "BTC-USDT", to avoid key issues
          fin_ut -- a timestamp, in ms, in UTC
        """
        assert "/" in pair_str, f"pair_str={pair_str} needs '/'"
        print(f"    Update rawohlcv file at exchange={exch_str}, pair={pair_str}.")

        filename = self._rawohlcv_filename(exch_str, pair_str)
        print(f"      filename={filename}")

        st_ut = self._calc_start_ut_maybe_delete(filename)
        print(f"      Aim to fetch data from start time: {pretty_timestr(st_ut)}")
        if st_ut > min(current_ut(), fin_ut):
            print("      Given start time, no data to gather. Exit.")
            return

        # empty ohlcv df
        df = initialize_rawohlcv_df()
        while True:
            print(f"      Fetch 1000 pts from {pretty_timestr(st_ut)}")
            exch = self.ss.exchs_dict[exch_str]
            raw_tohlcv_data = safe_fetch_ohlcv(
                exch,
                symbol=pair_str.replace("-", "/"),
                timeframe=self.pp.timeframe,
                since=st_ut,
                limit=1000,
            )
            if raw_tohlcv_data is None:  # exchange had error
                return
            uts = [vec[0] for vec in raw_tohlcv_data]
            if len(uts) > 1:
                # Ideally, time between ohclv candles is always 5m or 1h
                # But exchange data often has gaps. Warn about worst violations
                diffs_ms = np.array(uts[1:]) - np.array(uts[:-1])  # in ms
                diffs_m = diffs_ms / 1000 / 60  # in minutes
                mn_thr = self.pp.timeframe_m * OHLCV_MULT_MIN
                mx_thr = self.pp.timeframe_m * OHLCV_MULT_MAX

                if min(diffs_m) < mn_thr:
                    print(f"      **WARNING: short candle time: {min(diffs_m)} min")
                if max(diffs_m) > mx_thr:
                    print(f"      **WARNING: long candle time: {max(diffs_m)} min")

            # filter out data that's too new
            raw_tohlcv_data = [vec for vec in raw_tohlcv_data if vec[0] <= fin_ut]

            # concat both TOHLCV data
            next_df = pl.DataFrame(raw_tohlcv_data, schema=TOHLCV_SCHEMA_PL)
            df = concat_next_df(df, next_df)

            if len(raw_tohlcv_data) < 1000:  # no more data, we're at newest time
                break

            # prep next iteration
            newest_ut_value = df.tail(1)["timestamp"][0]

            print(f"      newest_ut_value: {newest_ut_value}")
            st_ut = newest_ut_value + self.pp.timeframe_ms

        # add "datetime" col, more
        df = transform_df(df)

        # output to file
        save_rawohlcv_file(filename, df)

    def _calc_start_ut_maybe_delete(self, filename: str) -> int:
        """
        @description
        Calculate start timestamp, reconciling whether file exists and where
        its data starts. Will delete file if it's inconvenient to re-use

        @arguments
          filename - csv file with data. May or may not exist.

        @return
          start_ut - timestamp (ut) to start grabbing data for
        """
        if not os.path.exists(filename):
            print("      No file exists yet, so will fetch all data")
            return self.ss.st_timestamp

        print("      File already exists")
        if not has_data(filename):
            print("      File has no data, so delete it")
            os.remove(filename)
            return self.ss.st_timestamp

        file_ut0, file_utN = oldest_ut(filename), newest_ut(filename)
        print(f"      File starts at: {pretty_timestr(file_ut0)}")
        print(f"      File finishes at: {pretty_timestr(file_utN)}")

        if self.ss.st_timestamp >= file_ut0:
            print("      User-specified start >= file start, so append file")
            return file_utN + self.pp.timeframe_ms

        print("      User-specified start < file start, so delete file")
        os.remove(filename)
        return self.ss.st_timestamp

    def _load_rawohlcv_files(self, fin_ut: int) -> Dict[str, Dict[str, pl.DataFrame]]:
        """
        @arguments
          fin_ut -- finish timestamp

        @return
          rawohlcv_dfs -- dict of [exch_str][pair_str] : df
            Where df has columns=OHLCV_COLS+"datetime", and index=timestamp
            And pair_str is eg "BTC/USDT". Not "BTC-USDT", to avoid key issues
        """
        print("  Load rawohlcv file.")
        st_ut = self.ss.st_timestamp

        rawohlcv_dfs: Dict[str, Dict[str, pl.DataFrame]] = {}  # [exch][pair] : df
        for exch_str in self.ss.exchange_strs:
            rawohlcv_dfs[exch_str] = {}

        for exch_str, pair_str in self.ss.exchange_pair_tups:
            assert "/" in pair_str, f"pair_str={pair_str} needs '/'"
            filename = self._rawohlcv_filename(exch_str, pair_str)
            cols = [
                signal_str  # cols is a subset of TOHLCV_COLS
                for e, signal_str, p in self.ss.input_feed_tups
                if e == exch_str and p == pair_str
            ]
            rawohlcv_df = load_rawohlcv_file(filename, cols, st_ut, fin_ut)

            assert "datetime" in rawohlcv_df.columns
            assert "timestamp" in rawohlcv_df.columns

            rawohlcv_dfs[exch_str][pair_str] = rawohlcv_df

        return rawohlcv_dfs

    def _rawohlcv_filename(self, exch_str, pair_str) -> str:
        """
        @description
          Computes a filename for the rawohlcv data.

        @arguments
          exch_str -- eg "binanceus"
          pair_str -- eg "BTC/USDT" or "BTC-USDT"

        @return
          rawohlcv_filename --

        @notes
          If pair_str has '/', it will become '-' in the filename.
        """
        assert "/" in pair_str or "-" in pair_str, pair_str
        pair_str = pair_str.replace("/", "-")  # filesystem needs "-"
        basename = f"{exch_str}_{pair_str}_{self.pp.timeframe}.parquet"
        filename = os.path.join(self.ss.parquet_dir, basename)
        return filename


@enforce_types
def _merge_rawohlcv_dfs(rawohlcv_dfs: dict) -> pl.DataFrame:
    """
    @arguments
      rawohlcv_dfs -- see class docstring

    @return
      mergedohlcv_df -- see class docstring
    """
    raw_dfs = rawohlcv_dfs

    print("  Merge rawohlcv dataframes.")
    merged_df = None
    for exch_str in raw_dfs.keys():
        for pair_str, raw_df in raw_dfs[exch_str].items():
            assert "/" in pair_str, f"pair_str={pair_str} needs '/'"
            assert "datetime" in raw_df.columns
            assert "timestamp" in raw_df.columns

            for raw_col in raw_df.columns:
                if raw_col in ["timestamp", "datetime"]:
                    continue
                signal_str = raw_col  # eg "close"
                merged_col = f"{exch_str}:{pair_str}:{signal_str}"
                merged_df = _add_df_col(merged_df, merged_col, raw_df, raw_col)

    merged_df = merged_df.select(_ordered_cols(merged_df.columns))  # type: ignore
    _verify_df_cols(merged_df)
    return merged_df


@enforce_types
def _add_df_col(
    merged_df: Union[pl.DataFrame, None],
    merged_col: str,  # eg "binance:BTC/USDT:close"
    raw_df: pl.DataFrame,
    raw_col: str,  # eg "close"
) -> pl.DataFrame:
    """
    Does polars equivalent of: merged_df[merged_col] = raw_df[raw_col].
    Tuned for this factory, by keeping "timestamp" & "datetime"
    """
    newraw_df = raw_df.with_columns(
        pl.col(raw_col).alias(merged_col),
    )
    newraw_df = newraw_df.select(["timestamp", merged_col, "datetime"])

    if merged_df is None:
        merged_df = newraw_df
    else:
        merged_df = merged_df.join(newraw_df, on=["timestamp", "datetime"], how="outer")
        merged_df = _merge_cols(merged_df, "timestamp", "timestamp_right")
        merged_df = _merge_cols(merged_df, "datetime", "datetime_right")

    merged_df = merged_df.select(_ordered_cols(merged_df.columns))  # type: ignore
    _verify_df_cols(merged_df)
    return merged_df


@enforce_types
def _merge_cols(df: pl.DataFrame, col1: str, col2: str) -> pl.DataFrame:
    """Keep the non-null versions of col1 & col2, in col1. Drop col2."""
    assert col1 in df
    if col2 not in df:
        return df
    for i in range(df.shape[1]):
        df[col1][i] = df[col1][i] or df[col2][i]
    df = df.drop(col2)
    return df


@enforce_types
def _ordered_cols(merged_cols: List[str]) -> List[str]:
    """Returns in order ["timestamp", item1, item2, item3, ..., "datetime"]"""
    assert "timestamp" in merged_cols
    assert "datetime" in merged_cols
    assert len(set(merged_cols)) == len(merged_cols)

    ordered_cols = []
    ordered_cols += ["timestamp"]
    ordered_cols += [col for col in merged_cols if col not in ["timestamp", "datetime"]]
    ordered_cols += ["datetime"]
    return ordered_cols


@enforce_types
def _verify_df_cols(df: pl.DataFrame):
    assert "datetime" in df.columns
    assert "timestamp" in df.columns
    for col in df.columns:
        assert "_right" not in col
        assert "_left" not in col
    assert df.columns == _ordered_cols(df.columns)
