import os

import numpy as np
import polars as pl
import pytest
from enforce_typing import enforce_types

from pdr_backend.lake.constants import (
    OHLCV_COLS,
    OHLCV_DTYPES_PL,
    TOHLCV_COLS,
    TOHLCV_DTYPES_PL,
    TOHLCV_SCHEMA_PL,
)
from pdr_backend.lake.plutil import (
    _get_tail_df,
    concat_next_df,
    has_data,
    initialize_rawohlcv_df,
    newest_ut,
    oldest_ut,
    save_rawohlcv_file,
    set_col_values,
    text_to_df,
    get_table_name,
    TableType,
)
from pdr_backend.lake.csv_data_store import CSVDataStore


FOUR_ROWS_RAW_TOHLCV_DATA = [
    [1686806100000, 1648.58, 1648.58, 1646.27, 1646.64, 7.4045],
    [1686806400000, 1647.05, 1647.05, 1644.61, 1644.86, 14.452],
    [1686806700000, 1644.57, 1646.41, 1642.49, 1645.81, 22.8612],
    [1686807000000, 1645.77, 1646.2, 1645.23, 1646.05, 8.1741],
]


ONE_ROW_RAW_TOHLCV_DATA = [[1686807300000, 1646, 1647.2, 1646.23, 1647.05, 8.1742]]


@enforce_types
def test_initialize_rawohlcv_df():
    df = initialize_rawohlcv_df()
    assert isinstance(df, pl.DataFrame)
    assert list(df.schema.values()) == TOHLCV_DTYPES_PL

    _assert_TOHLCVd_cols_and_types(df)

    # test with just 2 cols
    df = initialize_rawohlcv_df(OHLCV_COLS[:2])
    assert df.columns == OHLCV_COLS[:2]
    assert list(df.schema.values())[:2] == OHLCV_DTYPES_PL[:2]

    # test with just ut + 2 cols
    df = initialize_rawohlcv_df(TOHLCV_COLS[:3])
    assert df.columns == TOHLCV_COLS[:3]
    assert list(df.schema.values()) == TOHLCV_DTYPES_PL[:3]


@enforce_types
def test_set_col_values():
    df = pl.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        }
    )

    df2 = set_col_values(df, "a", [7, 8, 9])
    assert df2["a"].to_list() == [7, 8, 9]

    df2 = set_col_values(df, "a", [7.1, 8.1, 9.1])
    assert df2["a"].to_list() == [7.1, 8.1, 9.1]

    with pytest.raises(pl.exceptions.ShapeError):
        set_col_values(df, "a", [7, 8])


@enforce_types
def test_concat_next_df():
    # baseline data
    df = initialize_rawohlcv_df(TOHLCV_COLS)
    assert len(df) == 0

    cand_dtypes = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))
    schema = {col: cand_dtypes[col] for col in TOHLCV_COLS}

    next_df = pl.DataFrame(FOUR_ROWS_RAW_TOHLCV_DATA, schema=schema)
    assert len(next_df) == 4

    # add 4 rows to empty df
    df = concat_next_df(df, next_df)
    assert len(df) == 4

    _assert_TOHLCVd_cols_and_types(df)

    # assert 1 more row
    next_df = pl.DataFrame(ONE_ROW_RAW_TOHLCV_DATA, schema=schema)
    assert len(next_df) == 1

    # assert that concat verifies schemas match
    next_df = pl.DataFrame(ONE_ROW_RAW_TOHLCV_DATA, schema=schema)
    assert len(next_df) == 1
    assert "datetime" not in next_df.columns

    # add 1 row to existing 4 rows
    df = concat_next_df(df, next_df)
    assert len(df) == 4 + 1

    # assert concat order
    assert df.head(1)["timestamp"].to_list()[0] == FOUR_ROWS_RAW_TOHLCV_DATA[0][0]
    assert df.tail(1)["timestamp"].to_list()[0] == ONE_ROW_RAW_TOHLCV_DATA[0][0]
    _assert_TOHLCVd_cols_and_types(df)


@enforce_types
def _assert_TOHLCVd_cols_and_types(df: pl.DataFrame):
    assert df.columns == TOHLCV_COLS
    assert list(df.schema.values()) == TOHLCV_DTYPES_PL
    assert "timestamp" in df.columns and df.schema["timestamp"] == pl.Int64


def _filename(tmpdir) -> str:
    return os.path.join(tmpdir, "foo.csv")


@enforce_types
def test_load_basic(tmpdir):
    df = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    # TODO - fix foo.csv as filename
    file_id = "foo"

    # output to file
    CSVDataStore(str(tmpdir)).write(file_id, data=df, schema=TOHLCV_SCHEMA_PL)

    # simplest specification. Don't specify cols, st or fin
    df2 = CSVDataStore(str(tmpdir)).read(file_id)
    _assert_TOHLCVd_cols_and_types(df2)
    assert len(df2) == 4 and str(df) == str(df2)

    # explicitly specify cols, but not st or fin
    df2 = CSVDataStore(str(tmpdir)).read(file_id, schema=TOHLCV_SCHEMA_PL)
    _assert_TOHLCVd_cols_and_types(df2)
    assert len(df2) == 4 and str(df) == str(df2)

    # explicitly specify cols, st, fin
    df2 = CSVDataStore(str(tmpdir)).read(
        file_id, start_time=None, end_time=None, schema=TOHLCV_SCHEMA_PL
    )
    _assert_TOHLCVd_cols_and_types(df2)
    assert len(df2) == 4 and str(df) == str(df2)

    df2 = CSVDataStore(str(tmpdir)).read(
        file_id, start_time=0, end_time=np.inf, schema=TOHLCV_SCHEMA_PL
    )
    _assert_TOHLCVd_cols_and_types(df2)
    assert len(df2) == 4 and str(df) == str(df2)


@enforce_types
def test_load_append(tmpdir):
    # save 4-row parquet to new file
    # TODO - fix foo.csv as filename
    filename = "foo.csv"
    df_4_rows = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    CSVDataStore(str(tmpdir)).write(filename, data=df_4_rows)

    # append 1 row to existing file
    df_1_row = _df_from_raw_data(ONE_ROW_RAW_TOHLCV_DATA)
    CSVDataStore(str(tmpdir)).write(filename, data=df_1_row)

    # verify: doing a manual concat is the same as the load
    schema = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))
    df_1_row = pl.DataFrame(ONE_ROW_RAW_TOHLCV_DATA, schema=schema)
    df_5_rows = concat_next_df(df_4_rows, df_1_row)
    df_5_rows_loaded = CSVDataStore(str(tmpdir)).read(filename)

    _assert_TOHLCVd_cols_and_types(df_5_rows_loaded)

    assert len(df_5_rows_loaded) == 5
    assert str(df_5_rows) == str(df_5_rows_loaded)


@enforce_types
def test_load_filtered(tmpdir):
    # TODO - fix foo.csv as filename
    filename = "foo.csv"
    df = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    save_rawohlcv_file(filename, df)
    CSVDataStore(str(tmpdir)).write(filename, data=df)

    # load with filters on rows & columns
    timestamps = [row[0] for row in FOUR_ROWS_RAW_TOHLCV_DATA]
    cols = TOHLCV_COLS[:3]  # ["open", "high"]
    st = timestamps[1]  # 1686806400000
    fin = timestamps[2]  # 1686806700000

    # added functionality to filter by column
    df2 = CSVDataStore(str(tmpdir)).read(
        filename, start_time=st, end_time=fin, cols=cols
    )

    # test entries
    assert len(df2) == 2
    assert "timestamp" in df2.columns
    assert len(df2["timestamp"]) == 2
    assert df2["timestamp"].to_list() == timestamps[1:3]

    # test cols and types
    assert df2["timestamp"].dtype == pl.Int64
    assert list(df2.columns) == TOHLCV_COLS[:3]
    assert list(df2.schema.values()) == TOHLCV_DTYPES_PL[:3]


@enforce_types
def _df_from_raw_data(raw_data: list) -> pl.DataFrame:
    df = initialize_rawohlcv_df(TOHLCV_COLS)

    schema = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))
    next_df = pl.DataFrame(raw_data, schema=schema)

    df = concat_next_df(df, next_df)
    return df


@enforce_types
def test_has_data(tmpdir):
    filename0 = os.path.join(tmpdir, "f0.parquet")
    save_rawohlcv_file(filename0, _df_from_raw_data([]))
    assert not has_data(filename0)

    filename1 = os.path.join(tmpdir, "f1.parquet")
    save_rawohlcv_file(filename1, _df_from_raw_data(ONE_ROW_RAW_TOHLCV_DATA))
    assert has_data(filename1)

    filename4 = os.path.join(tmpdir, "f4.parquet")
    save_rawohlcv_file(filename4, _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA))
    assert has_data(filename4)


@enforce_types
def test_oldest_ut_and_newest_ut__with_data(tmpdir):
    filename = _filename(tmpdir)

    # write out four rows
    df = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    save_rawohlcv_file(filename, df)

    # assert head == oldest and tail == latest
    ut0 = oldest_ut(filename)
    utN = newest_ut(filename)

    assert ut0 == FOUR_ROWS_RAW_TOHLCV_DATA[0][0]
    assert utN == FOUR_ROWS_RAW_TOHLCV_DATA[-1][0]

    # append and check newest/oldest
    df = _df_from_raw_data(ONE_ROW_RAW_TOHLCV_DATA)
    save_rawohlcv_file(filename, df)

    ut0 = oldest_ut(filename)
    utN = newest_ut(filename)

    assert ut0 == FOUR_ROWS_RAW_TOHLCV_DATA[0][0]
    assert utN == ONE_ROW_RAW_TOHLCV_DATA[0][0]


@enforce_types
def test_oldest_ut_and_newest_ut__no_data(tmpdir):
    filename = _filename(tmpdir)
    df = _df_from_raw_data([])
    save_rawohlcv_file(filename, df)

    with pytest.raises(ValueError):
        oldest_ut(filename)
    with pytest.raises(ValueError):
        newest_ut(filename)


@enforce_types
def test_parquet_tail_records(tmpdir):
    df = pl.DataFrame(
        {
            "timestamp": [0, 1, 2, 3],
            "open": [100, 101, 102, 103],
            "high": [100, 101, 102, 103],
            "low": [100, 101, 102, 103],
            "close": [100, 101, 102, 103],
            "volume": [100, 101, 102, 103],
        }
    )

    filename = os.path.join(tmpdir, "foo.parquet")
    df.write_parquet(filename)

    target_tail_df = pl.DataFrame(
        {
            "timestamp": [3],
            "open": [103],
            "high": [103],
            "low": [103],
            "close": [103],
            "volume": [103],
        }
    )

    tail_df = _get_tail_df(filename, n=1)
    assert tail_df.equals(target_tail_df)


@enforce_types
def test_text_to_df():
    df = text_to_df(
        """timestamp|open|close
0|10.0|11.0
1|10.1|11.1
"""
    )
    assert df.columns == ["timestamp", "open", "close"]
    assert df.shape == (2, 3)
    assert df["timestamp"][0] == 0
    assert df["open"][1] == 10.1
    assert isinstance(df["open"][1], float)


@enforce_types
def test_get_table_name():
    table_name = get_table_name("test")
    assert table_name == "test"

    table_name = get_table_name("test", TableType.TEMP)
    assert table_name == "_temp_test"

    table_name = get_table_name("test", TableType.NORMAL)
    assert table_name == "test"

    table_name = get_table_name("test", TableType.ETL)
    assert table_name == "_etl_test"
