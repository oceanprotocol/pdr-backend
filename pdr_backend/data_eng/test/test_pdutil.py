import os

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import polars as pl
import pytest

from pdr_backend.data_eng.constants import (
    OHLCV_COLS,
    OHLCV_DTYPES,
    TOHLCV_COLS,
    TOHLCV_DTYPES,
    OHLCV_DTYPES_PL,
    TOHLCV_DTYPES_PL,
)
from pdr_backend.data_eng.pdutil import (
    initialize_df,
    transform_df,
    concat_next_df,
    save_parquet,
    load_parquet,
    has_data,
    oldest_ut,
    newest_ut,
    _get_tail_df,
)

FOUR_ROWS_RAW_TOHLCV_DATA = [
    [1686806100000, 1648.58, 1648.58, 1646.27, 1646.64, 7.4045],
    [1686806400000, 1647.05, 1647.05, 1644.61, 1644.86, 14.452],
    [1686806700000, 1644.57, 1646.41, 1642.49, 1645.81, 22.8612],
    [1686807000000, 1645.77, 1646.2, 1645.23, 1646.05, 8.1741],
]
ONE_ROW_RAW_TOHLCV_DATA = [[1686807300000, 1646, 1647.2, 1646.23, 1647.05, 8.1742]]


@enforce_types
def test_initialize_df():
    df = initialize_df()
    assert isinstance(df, pl.DataFrame)
    assert list(df.schema.values()) == TOHLCV_DTYPES_PL

    df = transform_df(df)
    _assert_TOHLCVd_cols_and_types(df)

    # test that it works with just 2 cols and without datetime
    df = initialize_df(OHLCV_COLS[:2])
    assert df.columns == OHLCV_COLS[:2]
    assert list(df.schema.values())[:2] == OHLCV_DTYPES_PL[:2]

    # test datetime w/ just ut + 2 cols
    df = initialize_df(TOHLCV_COLS[:3])
    df = transform_df(df)
    assert df.columns == TOHLCV_COLS[:3] + ["datetime"]
    assert list(df.schema.values()) == TOHLCV_DTYPES_PL[:3] + [
        pl.Datetime(time_unit="ms", time_zone="UTC")
    ]

    # assert error without timestamp
    df = initialize_df(OHLCV_COLS)
    with pytest.raises(Exception):
        df = transform_df(df)


@enforce_types
def test_concat_next_df():
    # baseline data
    df = initialize_df(TOHLCV_COLS)
    assert len(df) == 0

    cand_dtypes = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))
    schema = {col: cand_dtypes[col] for col in TOHLCV_COLS}

    next_df = pl.DataFrame(FOUR_ROWS_RAW_TOHLCV_DATA, schema=schema)
    assert len(next_df) == 4

    # add 4 rows to empty df
    df = concat_next_df(df, next_df)
    assert len(df) == 4

    # add datetime
    df = transform_df(df)
    _assert_TOHLCVd_cols_and_types(df)

    # from df with 4 rows, add 1 more row
    next_df = pl.DataFrame(ONE_ROW_RAW_TOHLCV_DATA, schema=schema)
    assert len(next_df) == 1

    # assert that concat verifies schemas match
    next_df = pl.DataFrame(ONE_ROW_RAW_TOHLCV_DATA, schema=schema)
    assert len(next_df) == 1
    assert "datetime" not in next_df.columns
    with pytest.raises(Exception):
        df = concat_next_df(df, next_df)

    # add datetime to next_df and concat both
    next_df = transform_df(next_df)
    df = concat_next_df(df, next_df)
    assert len(df) == 4 + 1
    _assert_TOHLCVd_cols_and_types(df)


@enforce_types
def _assert_TOHLCVd_cols_and_types(df: pl.DataFrame):
    assert df.columns == TOHLCV_COLS + ["datetime"]
    assert list(df.schema.values())[:-1] == TOHLCV_DTYPES_PL
    assert (
        str(list(df.schema.values())[-1]) == "Datetime(time_unit='ms', time_zone='UTC')"
    )
    assert "timestamp" in df.columns and df.schema["timestamp"] == pl.Int64


def _filename(tmpdir) -> str:
    return os.path.join(tmpdir, "foo.csv")


@enforce_types
def test_load_basic(tmpdir):
    filename = _filename(tmpdir)
    df = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    save_parquet(filename, df)

    # simplest specification. Don't specify cols, st or fin
    df2 = load_csv(filename)
    _assert_TOHLCVd_cols_and_types(df2)
    assert len(df2) == 4 and str(df) == str(df2)

    # explicitly specify cols, but not st or fin
    df2 = load_csv(filename, OHLCV_COLS)
    _assert_TOHLCVd_cols_and_types(df2)
    assert len(df2) == 4 and str(df) == str(df2)

    # explicitly specify cols, st, fin
    df2 = load_csv(filename, OHLCV_COLS, st=None, fin=None)
    _assert_TOHLCVd_cols_and_types(df2)
    assert len(df2) == 4 and str(df) == str(df2)

    df2 = load_csv(filename, OHLCV_COLS, st=0, fin=np.inf)
    _assert_TOHLCVd_cols_and_types(df2)
    assert len(df2) == 4 and str(df) == str(df2)


@enforce_types
def test_load_append(tmpdir):
    # save 4-row parquet
    filename = _filename(tmpdir)
    df_4_rows = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)

    # saving tohlcv w/o datetime throws an error
    with pytest.raises(Exception):
        save_parquet(filename, df_4_rows)  # write new file

    # transform then save
    df_4_rows = transform_df(df_4_rows)
    save_parquet(filename, df_4_rows)  # write new file

    # append 1 row to parquet
    df_1_row = _df_from_raw_data(ONE_ROW_RAW_TOHLCV_DATA)
    df_1_row = transform_df(df_1_row)
    save_parquet(filename, df_1_row)  # will append existing file

    # test that us doing a manual concat is the same as the load
    schema = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))
    df_5_rows = concat_next_df(
        df_4_rows, transform_df(pl.DataFrame(ONE_ROW_RAW_TOHLCV_DATA, schema=schema))
    )
    df_5_rows_loaded = load_parquet(filename)

    # we don't need to transform
    _assert_TOHLCVd_cols_and_types(df_5_rows_loaded)

    assert len(df_5_rows_loaded) == 5
    assert str(df_5_rows) == str(df_5_rows_loaded)


@enforce_types
def test_load_filtered(tmpdir):
    # save
    filename = _filename(tmpdir)
    df = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    df = transform_df(df)
    save_parquet(filename, df)

    # load with filters on rows & columns
    cols = OHLCV_COLS[:2]  # ["open", "high"]
    timestamps = [row[0] for row in FOUR_ROWS_RAW_TOHLCV_DATA]
    st = timestamps[1]  # 1686806400000
    fin = timestamps[2]  # 1686806700000
    df2 = load_parquet(filename, cols, st, fin)

    # test entries
    assert len(df2) == 2
    assert "timestamp" in df2.columns
    assert len(df2["timestamp"]) == 2
    assert df2["timestamp"].to_list() == timestamps[1:3]

    # test cols and types
    assert df2["timestamp"].dtype == pl.Int64
    assert list(df2.columns) == TOHLCV_COLS[:3] + ["datetime"]
    assert list(df2.schema.values())[:-1] == TOHLCV_DTYPES_PL[:3]
    assert (
        str(list(df2.schema.values())[-1])
        == "Datetime(time_unit='ms', time_zone='UTC')"
    )


@enforce_types
def _df_from_raw_data(raw_data: list):
    df = initialize_df(TOHLCV_COLS)

    schema = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))
    next_df = pl.DataFrame(raw_data, schema=schema)

    df = concat_next_df(df, next_df)
    return df


@enforce_types
def test_has_data(tmpdir):
    filename0 = os.path.join(tmpdir, "f0.csv")
    save_csv(filename0, _df_from_raw_data([]))
    assert not has_data(filename0)

    filename1 = os.path.join(tmpdir, "f1.csv")
    save_csv(filename1, _df_from_raw_data(ONE_ROW_RAW_TOHLCV_DATA))
    assert has_data(filename1)

    filename4 = os.path.join(tmpdir, "f4.csv")
    save_csv(filename4, _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA))
    assert has_data(filename4)


@enforce_types
def test_oldest_ut_and_newest_ut__with_data(tmpdir):
    filename = _filename(tmpdir)
    df = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    save_csv(filename, df)

    ut0 = oldest_ut(filename)
    utN = newest_ut(filename)
    assert ut0 == FOUR_ROWS_RAW_TOHLCV_DATA[0][0]
    assert utN == FOUR_ROWS_RAW_TOHLCV_DATA[-1][0]


@enforce_types
def test_oldest_ut_and_newest_ut__no_data(tmpdir):
    filename = _filename(tmpdir)
    df = _df_from_raw_data([])
    save_csv(filename, df)

    with pytest.raises(ValueError):
        oldest_ut(filename)
    with pytest.raises(ValueError):
        newest_ut(filename)


@enforce_types
def test_get_last_line(tmpdir):
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
    assert tail_df.frame_equal(target_tail_df)
