"""
plutil: polars dataframe & cvs utilities. 
These utilities are specific to the time-series dataframe columns we're using.
"""
import os
from typing import List

from enforce_typing import enforce_types
import numpy as np
import polars as pl

from pdr_backend.lake.constants import (
    OHLCV_COLS,
    TOHLCV_COLS,
    TOHLCV_SCHEMA_PL,
)


@enforce_types
def initialize_df(cols: List[str] = []) -> pl.DataFrame:
    """Start an empty df with the expected columns and schema
    Polars has no index, so "timestamp" and "datetime" are regular cols
    Applies transform to get columns (including datetime)
    """
    df = pl.DataFrame(data=[], schema=TOHLCV_SCHEMA_PL)
    df = df.select(cols if cols else "*")
    return df


@enforce_types
def transform_df(
    df: pl.DataFrame,
) -> pl.DataFrame:
    """Apply the transform on TOHLCV struct:
    - Ensure UTC timezone
    - Adds datetime
    """

    # preconditions
    assert "timestamp" in df.columns
    assert "datetime" not in df.columns

    # add datetime
    df = df.with_columns(
        [
            pl.from_epoch("timestamp", time_unit="ms")
            .dt.replace_time_zone("UTC")
            .alias("datetime")
        ]
    )
    return df


@enforce_types
def concat_next_df(df: pl.DataFrame, next_df: pl.DataFrame) -> pl.DataFrame:
    """Add a next_df to existing df, with the expected columns etc.
    Makes sure that both schemas match before concatenating.
    """
    assert df.schema == next_df.schema
    df = pl.concat([df, next_df])
    return df


@enforce_types
def save_rawohlcv_file(filename: str, df: pl.DataFrame):
    """write to parquet file
    parquet only supports appending via the pyarrow engine
    """
    # preconditions
    assert df.columns[:6] == TOHLCV_COLS
    assert "datetime" in df.columns

    # parquet column order: timestamp, datetime, O, H, L, C, V
    columns = ["timestamp", "datetime"] + OHLCV_COLS

    df = df.select(columns)

    if os.path.exists(filename):  # append existing file
        cur_df = pl.read_parquet(filename)
        df = pl.concat([cur_df, df])
        df.write_parquet(filename)
        n_new = df.shape[0] - cur_df.shape[0]
        print(f"  Just appended {n_new} df rows to file {filename}")
    else:  # write new file
        df.write_parquet(filename)
        print(f"  Just saved df with {df.shape[0]} rows to new file {filename}")


@enforce_types
def load_rawohlcv_file(filename: str, cols=None, st=None, fin=None) -> pl.DataFrame:
    """Load parquet file as a dataframe.

    Features:
    - Ensure that all dtypes are correct
    - Filter to just the input columns
    - Filter to just the specified start & end times
    - Memory stays reasonable

    @arguments
      cols -- what columns to use, eg ["open","high"]. Set to None for all cols.
      st -- starting timestamp, in ut. Set to 0 or None for very beginning
      fin -- ending timestamp, in ut. Set to inf or None for very end

    @return
      df -- dataframe

    @notes
      Polars does not have an index. "timestamp" is a regular col and required for "datetime"
      (1) Don't specify "datetime" as a column, as that'll get calc'd from timestamp

      Either don't save datetime, or save it and load it so it doesn't have to be re-computed.
    """
    # handle cols
    if cols is None:
        cols = TOHLCV_COLS
    if "timestamp" not in cols:
        cols = ["timestamp"] + cols
    assert "datetime" not in cols

    # set st, fin
    st = st if st is not None else 0
    fin = fin if fin is not None else np.inf

    # load tohlcv
    df = pl.read_parquet(
        filename,
        columns=cols,
    )
    df = df.filter((pl.col("timestamp") >= st) & (pl.col("timestamp") <= fin))

    # initialize df and enforce schema
    df0 = initialize_df(cols)
    df = concat_next_df(df0, df)

    # add in datetime column
    df = transform_df(df)

    # postconditions, return
    assert "timestamp" in df.columns and df["timestamp"].dtype == pl.Int64
    assert "datetime" in df.columns and df["datetime"].dtype == pl.Datetime

    return df


@enforce_types
def has_data(filename: str) -> bool:
    """Returns True if the file has >0 data entries"""
    df = pl.read_parquet(filename, n_rows=1)
    return not df.is_empty()


@enforce_types
def newest_ut(filename: str) -> int:
    """
    Return the timestamp for the youngest entry in the file.
    The latest date should be the tail (row = n), or last entry in the file/dataframe
    """
    df = _get_tail_df(filename, n=1)
    ut = int(df["timestamp"][0])
    return ut


@enforce_types
def _get_tail_df(filename: str, n: int = 5) -> pl.DataFrame:
    """Returns the last record in a parquet file, as a list"""

    df = pl.read_parquet(filename)
    tail_df = df.tail(n)
    if not tail_df.is_empty():
        return tail_df
    raise ValueError(f"File {filename} has no entries")


@enforce_types
def oldest_ut(filename: str) -> int:
    """
    Return the timestamp for the oldest entry in the parquet file.
    The oldest date should be the head (row = 0), or the first entry in the file/dataframe
    """
    df = _get_head_df(filename, n=1)
    ut = int(df["timestamp"][0])
    return ut


@enforce_types
def _get_head_df(filename: str, n: int = 5) -> pl.DataFrame:
    """Returns the head of parquet file, as a df"""
    df = pl.read_parquet(filename)
    head_df = df.head(n)
    if not head_df.is_empty():
        return head_df
    raise ValueError(f"File {filename} has no entries")
