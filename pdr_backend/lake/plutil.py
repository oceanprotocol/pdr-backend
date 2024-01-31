"""
plutil: polars dataframe & csv/parquet utilities. 
These utilities are specific to the time-series dataframe columns we're using.
"""

import os
import shutil
from io import StringIO
from tempfile import mkdtemp
from typing import List, Dict, Optional

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
def _transform_timestamp_to_ms_lazy(lazy_df: pl.LazyFrame) -> pl.LazyFrame:
    """
    Transform timestamp to ms
    @precondition
        lazy_df must have a column named "timestamp"

    @description
        Transform timestamp to ms

    @return
        lazy_df with timestamp column transformed to ms
    """

    lazy_df = lazy_df.with_columns(pl.col("timestamp").mul(1000).alias("timestamp"))
    return lazy_df


@enforce_types
def _filter_with_timestamps_lazy(
    lazy_df: pl.LazyFrame, st_ut: int, fin_ut: int
) -> pl.LazyFrame:
    """
    @precondition
        lazy_df must have a column named "timestamp"

    @arguments
        st_ut -- start timestamp in ms
        fin_ut -- finish timestamp in ms

    @description
        Filter lazy_df with timestamps
        + Cull any records outside of our time range
        + Sort them by timestamp

    @return
        lazy_df with timestamps filtered and sorted
    """

    lazy_df = lazy_df.filter(pl.col("timestamp").is_between(st_ut, fin_ut)).sort(
        "timestamp"
    )
    return lazy_df


@enforce_types
def _filter_and_sort_pdr_records(
    df: pl.DataFrame, st_ut: int, fin_ut: int
) -> pl.DataFrame:
    """
    @description
        A wrapper for _filter_with_timestamps_lazy and _sort_by_timestamp_lazy
        it takes a dataframe and filters and sorts it by timestamp
        and returns the dataframe

    @arguments
        df -- dataframe
        st_ut -- start timestamp in seconds
        fin_ut -- finish timestamp in seconds

    @return
        df -- dataframe with timestamps filtered and sorted
    """
    lazy_df = df.lazy()
    lazy_df = _transform_timestamp_to_ms_lazy(lazy_df)
    lazy_df = _filter_with_timestamps_lazy(lazy_df, st_ut, fin_ut)
    return lazy_df.collect()


@enforce_types
def check_df_len(
    lazy_df: pl.LazyFrame,
    min_len: Optional[int],
    max_len: Optional[int],
    identifier: str = "df",
):
    """
    @description
        Check if lazy_df has the right number of records
        + If not, raise an error

    @arguments
        lazy_df -- dataframe
        min_len -- minimum number of records
        max_len -- maximum number of records

    @return
        void
    """
    df_shape_row_count = lazy_df.collect().shape[0]
    if max_len is not None:
        assert (
            df_shape_row_count <= max_len
        ), f"{identifier} has {df_shape_row_count} records, but should have at most {max_len} records"  # pylint: disable=line-too-long
    if min_len is not None:
        assert (
            df_shape_row_count >= min_len
        ), f"{identifier} has {df_shape_row_count} records, but should have at least {min_len} records"  # pylint: disable=line-too-long

    assert (
        df_shape_row_count > 0
    ), f"No records to summarize {identifier}. Please adjust params."


def _transform_timestamp_to_ms(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(
        [
            pl.col("timestamp").mul(1000).alias("timestamp"),
        ]
    )
    return df
