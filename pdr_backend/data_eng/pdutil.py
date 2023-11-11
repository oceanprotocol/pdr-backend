"""
pdutil: pandas dataframe & cvs utilities. 
These utilities are specific to the time-series dataframe columns we're using.
"""
import os
from typing import List

from enforce_typing import enforce_types
import numpy as np
import pandas as pd

from pdr_backend.data_eng.constants import (
    OHLCV_COLS,
    TOHLCV_COLS,
    TOHLCV_DTYPES,
)


@enforce_types
def initialize_df(cols: List[str]) -> pd.DataFrame:
    """Start a new df, with the expected columns, index, and dtypes
    It's ok whether cols has "timestamp" or not. Same for "datetime".
    The return df has "timestamp" for index and "datetime" as col
    """
    dtypes = {
        col: pd.Series(dtype=dtype)
        for col, dtype in zip(TOHLCV_COLS, TOHLCV_DTYPES)
        if col in cols or col == "timestamp"
    }
    df = pd.DataFrame(dtypes)
    df = df.set_index("timestamp")
    # pylint: disable=unsupported-assignment-operation
    df["datetime"] = pd.to_datetime(df.index.values, unit="ms", utc=True)

    return df


@enforce_types
def concat_next_df(df: pd.DataFrame, next_df: pd.DataFrame) -> pd.DataFrame:
    """Add a next df to existing df, with the expected columns etc.
    The existing df *should* have the 'datetime' col, and next_df should *not*.
    """
    assert "datetime" in df.columns
    assert "datetime" not in next_df.columns
    next_df = next_df.set_index("timestamp")
    next_df["datetime"] = pd.to_datetime(next_df.index.values, unit="ms", utc=True)
    df = pd.concat([df, next_df])
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
    assert "timestamp" not in df.columns
    assert df.index.name == "timestamp" and df.index.dtype == np.int64
    assert "datetime" in df.columns
    return df


@enforce_types
def has_data(filename: str) -> bool:
    """Returns True if the file has >0 data entries"""
    with open(filename) as f:
        for i, _ in enumerate(f):
            if i >= 1:
                return True
    return False


@enforce_types
def oldest_ut(filename: str) -> int:
    """
    Return the timestamp for the oldest entry in the file.
    Assumes the oldest entry is the second line in the file.
    (First line is header)
    """
    line = _get_second_line(filename)
    ut = int(line.split(",")[0])
    return ut


@enforce_types
def _get_second_line(filename) -> str:
    """Returns the last line in a file, as a string"""
    with open(filename) as f:
        for i, line in enumerate(f):
            if i == 1:
                return line
    raise ValueError(f"File {filename} has no entries")


@enforce_types
def newest_ut(filename: str) -> int:
    """
    Return the timestamp for the youngest entry in the file.
    Assumes the youngest entry is the very last line in the file.
    """
    line = _get_last_line(filename)
    ut = int(line.split(",")[0])
    return ut


@enforce_types
def _get_last_line(filename: str) -> str:
    """Returns the last line in a file, as a string"""
    line = None
    with open(filename) as f:
        for line in f:
            pass
    return line if line is not None else ""
