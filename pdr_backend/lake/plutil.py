"""
plutil: polars dataframe & csv/parquet utilities. 
These utilities are specific to the time-series dataframe columns we're using.
"""
import os
import shutil
from io import StringIO
from tempfile import mkdtemp
from typing import List, Dict, Iterable, Union, Tuple

import numpy as np
import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.constants import TOHLCV_COLS, TOHLCV_SCHEMA_PL


@enforce_types
def initialize_rawohlcv_df(cols: List[str] = []) -> pl.DataFrame:
    """Start an empty df with the expected columns and schema
    Applies transform to get columns
    """
    df = pl.DataFrame(data=[], schema=TOHLCV_SCHEMA_PL)
    df = df.select(cols if cols else "*")
    return df


@enforce_types
def set_col_values(df: pl.DataFrame, col: str, new_vals: list) -> pl.DataFrame:
    """Equivalent to: df[col] = new_vals"""
    return df.with_columns(pl.Series(new_vals).alias(col))


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
    assert "datetime" not in df.columns

    # parquet column order: timestamp, O, H, L, C, V
    columns = TOHLCV_COLS

    df = df.select(columns)

    if os.path.exists(filename):  # append existing file
        cur_df = pl.read_parquet(filename)
        df = pl.concat([cur_df, df])
        df.write_parquet(filename)
        n_new = df.shape[0] - cur_df.shape[0]
        print(f"      Just appended {n_new} df rows to file {filename}")
    else:  # write new file
        df.write_parquet(filename)
        print(f"      Just saved df with {df.shape[0]} rows to new file {filename}")


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
      Polars does not have an index. "timestamp" is a regular col
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
    df0 = initialize_rawohlcv_df(cols)
    df = concat_next_df(df0, df)

    # postconditions, return
    assert "timestamp" in df.columns and df["timestamp"].dtype == pl.Int64
    assert "datetime" not in df.columns

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


@enforce_types
def text_to_df(s: str) -> pl.DataFrame:
    tmpdir = mkdtemp()
    filename = os.path.join(tmpdir, "df.psv")
    s = StringIO(s)  # type: ignore
    with open(filename, "w") as f:
        for line in s:
            f.write(line)
    df = pl.scan_csv(filename, separator="|").collect()
    shutil.rmtree(tmpdir)
    return df


@enforce_types
def _object_list_to_df(objects: List[object], schema: Dict) -> pl.DataFrame:
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
def left_join_with(
    target: pl.DataFrame,
    other: pl.DataFrame,
    left_on: str = "ID",
    right_on: str = "ID",
    w_columns: Iterable[Union[pl.Expr, str]] = [],
    select_columns: Iterable[Union[pl.Expr, str]] = [],
) -> pl.DataFrame:
    """
    @description
        Left join two dataframes, and select the columns from the right dataframe
        to be added to the left dataframe.
    @arguments
        target -- dataframe to be joined with
        other -- dataframe to join with
        with_columns -- columns to create
        select_columns -- columns to select from the right dataframe
    @returns
        joined dataframe
    """
    return (
        target.join(other, left_on=left_on, right_on=right_on, how="left")
        .with_columns(w_columns)
        .select(select_columns)
    )


@enforce_types
def pick_df_and_ids_on_period(
    target: pl.DataFrame,
    start_timestamp: int,
    finish_timestamp: int,
) -> Tuple[pl.DataFrame, List[str]]:
    """
    @description
        Filter dataframe with timestamp and return the ID list.
    @arguments
        target -- dataframe to be filtered
        start_timestamp -- start timestamp
        finish_timestamp -- finish timestamp
    @returns
        Filtered dataframe and ID list
    """
    target = target.filter(
        (pl.col("timestamp") >= start_timestamp)
        & (pl.col("timestamp") <= finish_timestamp)
    )
    return (target, target["ID"].to_list())


@enforce_types
def filter_and_drop_columns(
    df: pl.DataFrame, target_column: str, ids: List[str], columns_to_drop: List[str]
) -> pl.DataFrame:
    """
    @description
        Filter dataframe based on ID and drop specified columns.
    @arguments
        df -- dataframe to be filtered and modified
        target_column -- column to filter on
        ids -- list of IDs to filter
        columns_to_drop -- list of columns to drop
    @returns
        Modified dataframe
    """
    return df.filter(pl.col(target_column).is_in(ids)).drop(columns_to_drop)
