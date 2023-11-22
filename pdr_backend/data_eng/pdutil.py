"""
pdutil: pandas dataframe & cvs utilities. 
These utilities are specific to the time-series dataframe columns we're using.
"""
import os
from typing import List

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import polars as pl
from polars import col
import pyarrow.dataset as ds

from pdr_backend.data_eng.constants import (
    OHLCV_COLS,
    TOHLCV_COLS,
    TOHLCV_DTYPES,
    TOHLCV_DTYPES_PL,
)


# TODO: Move this implementation to data_factory.ohlcv module
@enforce_types
def initialize_df(cols: List[str] = None) -> pl.DataFrame:
    """Start an empty df with the expected columns and schema
    Polars has no index, so "timestamp" and "datetime" are regular cols
    Applies transform to get columns (including datetime)
    """

    # define schema
    schema = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))

    # create df
    df = pl.DataFrame(data=[], schema=schema).select(cols if cols else "*")
    return df


# TODO: Move this implementation to data_factory.ohlcv module
def transform_df(
    df: pl.DataFrame,
) -> pl.DataFrame:
    """Apply the transform on TOHLCV struct.
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


# TODO: Make this only check schemas and concat
@enforce_types
def concat_next_df(df: pl.DataFrame, next_df: pl.DataFrame) -> pl.DataFrame:
    """Add a next_df to existing df, with the expected columns etc.
    Makes sure that both schemas match before concatenating.
    """
    assert df.schema == next_df.schema
    df = pl.concat([df, next_df])
    return df


@enforce_types
def save_csv(filename: str, df: pd.DataFrame):
    """Append to csv file if it exists, otherwise create new one.
    With header=True and index=True, it will set the index_col too
    """
    # preconditions
    assert df.columns.tolist() == OHLCV_COLS + ["datetime"]

    # csv column order: timestamp (index), datetime, O, H, L, C, V
    columns = ["datetime"] + OHLCV_COLS

    if os.path.exists(filename):  # append existing file
        df.to_csv(filename, mode="a", header=False, index=True, columns=columns)
        print(f"  Just appended {df.shape[0]} df rows to file {filename}")
    else:  # write new file
        df.to_csv(filename, mode="w", header=True, index=True, columns=columns)
        print(f"  Just saved df with {df.shape[0]} rows to new file {filename}")


@enforce_types
def load_csv(filename: str, cols=None, st=None, fin=None) -> pd.DataFrame:
    """Load csv file as a dataframe.

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
      Don't specify "timestamp" as a column because it's the df *index*
      Don't specify "datetime" as a column, as that'll get calc'd from timestamp
    """
    if cols is None:
        cols = OHLCV_COLS
    assert "timestamp" not in cols
    assert "datetime" not in cols
    cols = ["timestamp"] + cols

    # set skiprows, nrows
    if st in [0, None] and fin in [np.inf, None]:
        skiprows, nrows = None, None
    else:
        df0 = pd.read_csv(filename, usecols=["timestamp"])
        timestamps = df0["timestamp"].tolist()
        skiprows = [
            i + 1 for i, timestamp in enumerate(timestamps) if timestamp < st
        ]  # "+1" to account for header
        if skiprows == []:
            skiprows = None
        nrows = sum(
            1 for row, timestamp in enumerate(timestamps) if st <= timestamp <= fin
        )

    # set dtypes
    cand_dtypes = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES))
    dtypes = {col: cand_dtypes[col] for col in cols}

    # load
    df = pd.read_csv(
        filename,
        dtype=dtypes,
        usecols=cols,
        skiprows=skiprows,
        nrows=nrows,
    )

    # add in datetime column
    df0 = initialize_df(cols)
    df = concat_next_df(df0, df)

    # postconditions, return
    assert "timestamp" in df.columns and df["timestamp"].dtype == pl.int64
    assert "datetime" in df.columns and df["datetime"].dtype == pl.Datetime
    return df


# TODO - Move ohlcv logic out, keep util generic
@enforce_types
def save_parquet(filename: str, df: pl.DataFrame):
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
        # TODO: Implement parquet-append with pyarrow
        cur_df = pl.read_parquet(filename)
        df = pl.concat([cur_df, df])
        df.write_parquet(filename)
        print(f"  Just appended {df.shape[0]} df rows to file {filename}")
    else:  # write new file
        df.write_parquet(filename)
        print(f"  Just saved df with {df.shape[0]} rows to new file {filename}")


# TODO - Move ohlcv logic out, keep util generic
@enforce_types
def load_parquet(filename: str, cols=None, st=None, fin=None) -> pl.DataFrame:
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

      TODO: Fix (1), save_parquet already saves out dataframe.
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
    # TODO: Helper to go from np<->pl schema/dtypes
    assert "timestamp" in df.columns and df["timestamp"].dtype == pl.Int64
    assert "datetime" in df.columns and df["datetime"].dtype == pl.Datetime

    return df


@enforce_types
def has_data(filename: str) -> bool:
    """Returns True if the file has >0 data entries"""
    df = pl.read_parquet(filename, n_rows=1)
    return not df.is_empty()


@enforce_types
def oldest_ut(filename: str) -> int:
    """
    Return the timestamp for the oldest entry in the parquet file.
    Assumes the oldest entry is the last() row.
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
def newest_ut(filename: str) -> int:
    """
    Return the timestamp for the youngest entry in the file.
    Assumes the youngest entry is the very last line in the file.
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
