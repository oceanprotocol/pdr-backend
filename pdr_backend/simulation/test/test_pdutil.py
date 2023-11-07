import os

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import pytest

from pdr_backend.simulation.constants import (
    OHLCV_COLS,
    OHLCV_DTYPES,
    TOHLCV_COLS,
)
from pdr_backend.simulation.pdutil import (
    initialize_df,
    concat_next_df,
    save_csv,
    load_csv,
    has_data,
    oldest_ut,
    newest_ut,
    _get_last_line,
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
    df = initialize_df(TOHLCV_COLS)

    assert isinstance(df, pd.DataFrame)
    _assert_TOHLCVd_cols_and_types(df)

    df = initialize_df(OHLCV_COLS[:2])
    assert df.columns.tolist() == OHLCV_COLS[:2] + ["datetime"]
    assert df.dtypes.tolist()[:-1] == OHLCV_DTYPES[:2]


@enforce_types
def test_concat_next_df():
    # baseline data
    df = initialize_df(TOHLCV_COLS)
    assert len(df) == 0

    next_df = pd.DataFrame(FOUR_ROWS_RAW_TOHLCV_DATA, columns=TOHLCV_COLS)
    assert len(next_df) == 4

    # add 4 rows to empty df
    df = concat_next_df(df, next_df)
    assert len(df) == 4
    _assert_TOHLCVd_cols_and_types(df)

    # from df with 4 rows, add 1 more row
    next_df = pd.DataFrame(ONE_ROW_RAW_TOHLCV_DATA, columns=TOHLCV_COLS)
    assert len(next_df) == 1

    df = concat_next_df(df, next_df)
    assert len(df) == 4 + 1
    _assert_TOHLCVd_cols_and_types(df)


@enforce_types
def _assert_TOHLCVd_cols_and_types(df: pd.DataFrame):
    assert df.columns.tolist() == OHLCV_COLS + ["datetime"]
    assert df.dtypes.tolist()[:-1] == OHLCV_DTYPES
    assert str(df.dtypes.tolist()[-1]) == "datetime64[ns, UTC]"
    assert df.index.name == "timestamp" and df.index.dtype == np.int64


def _filename(tmpdir) -> str:
    return os.path.join(tmpdir, "foo.csv")


@enforce_types
def test_load_basic(tmpdir):
    filename = _filename(tmpdir)
    df = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    save_csv(filename, df)

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
    # save 4-row csv
    filename = _filename(tmpdir)
    df_4_rows = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    save_csv(filename, df_4_rows)  # write new file

    # append 1 row to csv
    df_1_row = _df_from_raw_data(ONE_ROW_RAW_TOHLCV_DATA)
    save_csv(filename, df_1_row)  # will append existing file

    # test
    df_5_rows = concat_next_df(
        df_4_rows, pd.DataFrame(ONE_ROW_RAW_TOHLCV_DATA, columns=TOHLCV_COLS)
    )
    df_5_rows_loaded = load_csv(filename)
    _assert_TOHLCVd_cols_and_types(df_5_rows_loaded)
    assert len(df_5_rows_loaded) == 5
    assert str(df_5_rows) == str(df_5_rows_loaded)


@enforce_types
def test_load_filtered(tmpdir):
    # save
    filename = _filename(tmpdir)
    df = _df_from_raw_data(FOUR_ROWS_RAW_TOHLCV_DATA)
    save_csv(filename, df)

    # load with filters on rows & columns
    cols = OHLCV_COLS[:2]  # ["open", "high"]
    timestamps = [row[0] for row in FOUR_ROWS_RAW_TOHLCV_DATA]
    st = timestamps[1]  # 1686806400000
    fin = timestamps[2]  # 1686806700000
    df2 = load_csv(filename, cols, st, fin)

    # test entries
    assert len(df2) == 2
    assert len(df2.index.values) == 2
    assert df2.index.values.tolist() == timestamps[1:3]

    # test cols and types
    assert df2.columns.tolist() == OHLCV_COLS[:2] + ["datetime"]
    assert df2.dtypes.tolist()[:-1] == OHLCV_DTYPES[:2]
    assert str(df2.dtypes.tolist()[-1]) == "datetime64[ns, UTC]"
    assert df2.index.name == "timestamp"
    assert df2.index.dtype == np.int64


@enforce_types
def _df_from_raw_data(raw_data: list):
    df = initialize_df(OHLCV_COLS)
    next_df = pd.DataFrame(raw_data, columns=TOHLCV_COLS)
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
    filename = os.path.join(tmpdir, "foo.csv")

    with open(filename, "w") as f:
        f.write(
            """line0 boo bo bum
line1 foo bar
line2 bah bah
line3 ha ha lol"""
        )
    target_last_line = "line3 ha ha lol"
    found_last_line = _get_last_line(filename)
    assert found_last_line == target_last_line
