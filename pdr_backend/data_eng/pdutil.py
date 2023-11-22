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
import pyarrow.dataset as ds

from pdr_backend.data_eng.constants import (
    OHLCV_COLS,
    TOHLCV_COLS,
    TOHLCV_DTYPES,
)


@enforce_types
def initialize_df(cols: List[str]) -> pl.DataFrame:
    """Start a new df, with the expected columns, index, and dtypes
    It's ok whether cols has "timestamp" or not. Same for "datetime".
    The return df has "timestamp" for index and "datetime" as col
    """
    dtypes = {
        col: pd.Series(dtype=dtype)
        for col, dtype in zip(TOHLCV_COLS, TOHLCV_DTYPES)
        if col in cols or col == "timestamp"
    }
    df = pl.DataFrame(dtypes)
    df = df.with_columns([pl.from_epoch("timestamp", time_unit="ms").alias("datetime")])

    return df


@enforce_types
def concat_next_df(df: pl.DataFrame, next_df: pl.DataFrame) -> pl.DataFrame:
    """Add a next df to existing df, with the expected columns etc.
    The existing df *should* have the 'datetime' col, and next_df should *not*.
    """
    assert "datetime" in df.columns
    assert "datetime" not in next_df.columns
    next_df = next_df.with_columns(
        [pl.from_epoch("timestamp", time_unit="ms").alias("datetime")]
    )

    print("df.columns", df)
    print("next_df.columns", next_df)

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


@enforce_types
def save_parquet(filename: str, df: pl.DataFrame):
    """write to parquet file
    parquet only supports appending via the pyarrow engine
    """
    # preconditions
    assert df.columns == TOHLCV_COLS + ["datetime"]

    # parquet column order: timestamp (index), datetime, O, H, L, C, V
    columns = ["datetime"] + TOHLCV_COLS

    df = df.select(columns)
    if os.path.exists(filename):  # append existing file
        # TODO - Implement parquet-append with pyarrow
        cur_df = pl.read_parquet(filename)
        df = pl.concat([cur_df, df])
        df.write_parquet(filename)
        print(f"  Just appended {df.shape[0]} df rows to file {filename}")
    else:  # write new file
        df.write_parquet(filename)
        print(f"  Just saved df with {df.shape[0]} rows to new file {filename}")


@enforce_types
def load_parquet(filename: str, cols=None, st=None, fin=None) -> pd.DataFrame:
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
      Don't specify "timestamp" as a column because it's the df *index*
      Don't specify "datetime" as a column, as that'll get calc'd from timestamp
    """
    if cols is None:
        cols = OHLCV_COLS
    assert "timestamp" not in cols
    assert "datetime" not in cols
    cols = ["timestamp"] + cols

    # set dtypes
    cand_dtypes = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES))
    dtypes = {col: cand_dtypes[col] for col in cols}

    # load
    df = pl.read_parquet(
        filename,
        columns=cols,
    ).with_columns(dtypes)

    st = st if st is not None else 0
    fin = fin if fin is not None else np.inf
    df = df.filter((pl.col("timestamp") >= st) & (pl.col("timestamp") <= fin))

    # add in datetime column
    df0 = initialize_df(cols)
    df = concat_next_df(df0, df)

    # postconditions, return
    # TODO - Resolve for np.int64 vs pl.Int64
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
