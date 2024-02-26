import numpy as np
import pandas as pd
import polars as pl
import pytest
from enforce_typing import enforce_types

from pdr_backend.util.mathutil import (
    all_nan,
    fill_nans,
    has_nan,
    nmse,
    round_sig,
    string_to_bytes32,
)
from pdr_backend.util.currency_types import Eth, Wei


@enforce_types
def test_round_sig():
    assert round_sig(123456, 1) == 100000
    assert round_sig(123456, 2) == 120000
    assert round_sig(123456, 3) == 123000
    assert round_sig(123456, 4) == 123500
    assert round_sig(123456, 5) == 123460
    assert round_sig(123456, 6) == 123456

    assert round_sig(1.23456, 1) == 1.00000
    assert round_sig(1.23456, 2) == 1.20000
    assert round_sig(1.23456, 3) == 1.23000
    assert round_sig(1.23456, 4) == 1.23500
    assert round_sig(1.23456, 5) == 1.23460
    assert round_sig(1.23456, 6) == 1.23456

    assert round_sig(1.23456e9, 1) == 1.00000e9
    assert round_sig(1.23456e9, 2) == 1.20000e9
    assert round_sig(1.23456e9, 3) == 1.23000e9
    assert round_sig(1.23456e9, 4) == 1.23500e9
    assert round_sig(1.23456e9, 5) == 1.23460e9
    assert round_sig(1.23456e9, 6) == 1.23456e9


@enforce_types
def test_all_nan__or_None():
    # 1d array
    assert not all_nan(np.array([1.0, 2.0, 3.0, 4.0]))
    assert not all_nan(np.array([1.0, None, 3.0, 4.0]))
    assert not all_nan(np.array([1.0, 2.0, np.nan, 4.0]))
    assert not all_nan(np.array([1.0, None, np.nan, 4.0]))
    assert all_nan(np.array([None, None, None, None]))
    assert all_nan(np.array([np.nan, np.nan, np.nan, None]))
    assert all_nan(np.array([np.nan, np.nan, np.nan, np.nan]))

    # 2d array
    assert not all_nan(np.array([[1.0, 2.0], [3.0, 4.0]]))
    assert not all_nan(np.array([[1.0, None], [3.0, 4.0]]))
    assert not all_nan(np.array([[1.0, 2.0], [np.nan, 4.0]]))
    assert not all_nan(np.array([[1.0, None], [np.nan, 4.0]]))
    assert all_nan(np.array([[None, None], [None, None]]))
    assert all_nan(np.array([[np.nan, np.nan], [np.nan, None]]))
    assert all_nan(np.array([[np.nan, np.nan], [np.nan, np.nan]]))

    # pd Series
    assert not all_nan(pd.Series([1.0, 2.0, 3.0, 4.0]))
    assert not all_nan(pd.Series([1.0, None, 3.0, 4.0]))
    assert not all_nan(pd.Series([1.0, 2.0, np.nan, 4.0]))
    assert not all_nan(pd.Series([1.0, None, np.nan, 4.0]))
    assert all_nan(pd.Series([None, None, None, None]))
    assert all_nan(pd.Series([np.nan, np.nan, np.nan, None]))
    assert all_nan(pd.Series([np.nan, np.nan, np.nan, np.nan]))

    # pd DataFrame
    assert not all_nan(pd.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0]}))
    assert not all_nan(pd.DataFrame({"A": [1.0, None], "B": [3.0, 4.0]}))
    assert not all_nan(pd.DataFrame({"A": [1.0, 2.0], "B": [np.nan, 4.0]}))
    assert not all_nan(pd.DataFrame({"A": [1.0, None], "B": [np.nan, 4.0]}))
    assert all_nan(pd.DataFrame({"A": [None, None], "B": [None, None]}))
    assert all_nan(pd.DataFrame({"A": [np.nan, np.nan], "B": [np.nan, None]}))
    assert all_nan(pd.DataFrame({"A": [np.nan, np.nan], "B": [np.nan, np.nan]}))

    # pl Series
    assert not all_nan(pl.Series([1.0, 2.0, 3.0, 4.0]))
    assert not all_nan(pl.Series([1.0, None, 3.0, 4.0]))
    assert not all_nan(pl.Series([1.0, 2.0, np.nan, 4.0]))
    assert not all_nan(pl.Series([1.0, None, np.nan, 4.0]))
    assert all_nan(pl.Series([None, None, None, None]))
    assert all_nan(pl.Series([np.nan, np.nan, np.nan, None]))
    assert all_nan(pl.Series([np.nan, np.nan, np.nan, np.nan]))

    # pl DataFrame
    assert not all_nan(pl.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0]}))
    assert not all_nan(pl.DataFrame({"A": [1.0, None], "B": [3.0, 4.0]}))
    assert not all_nan(pl.DataFrame({"A": [1.0, 2.0], "B": [np.nan, 4.0]}))
    assert not all_nan(pl.DataFrame({"A": [1.0, None], "B": [np.nan, 4.0]}))
    assert all_nan(pl.DataFrame({"A": [None, None], "B": [None, None]}))
    assert all_nan(pl.DataFrame({"A": [np.nan, np.nan], "B": [np.nan, None]}))
    assert all_nan(pl.DataFrame({"A": [np.nan, np.nan], "B": [np.nan, np.nan]}))


@enforce_types
def test_has_nan__or_None():
    # 1d array
    assert not has_nan(np.array([1.0, 2.0, 3.0, 4.0]))
    assert has_nan(np.array([1.0, 2.0, np.nan, 4.0]))
    assert has_nan(np.array([1.0, None, 3.0, 4.0]))
    assert has_nan(np.array([1.0, None, np.nan, 4.0]))

    # 2d array
    assert not has_nan(np.array([[1.0, 2.0], [3.0, 4.0]]))
    assert has_nan(np.array([[1.0, 2.0], [np.nan, 4.0]]))
    assert has_nan(np.array([[1.0, None], [3.0, 4.0]]))
    assert has_nan(np.array([[1.0, None], [np.nan, 4.0]]))

    # pd Series
    assert not has_nan(pd.Series([1.0, 2.0, 3.0, 4.0]))
    assert has_nan(pd.Series([1.0, 2.0, np.nan, 4.0]))
    assert has_nan(pd.Series([1.0, None, 3.0, 4.0]))
    assert has_nan(pd.Series([1.0, None, np.nan, 4.0]))

    # pd DataFrame
    assert not has_nan(pd.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0]}))
    assert has_nan(pd.DataFrame({"A": [1.0, 2.0], "B": [np.nan, 4.0]}))
    assert has_nan(pd.DataFrame({"A": [1.0, None], "B": [3.0, 4.0]}))
    assert has_nan(pd.DataFrame({"A": [1.0, None], "B": [np.nan, 4.0]}))

    # pl Series
    assert not has_nan(pl.Series([1.0, 2.0, 3.0, 4.0]))
    assert has_nan(pl.Series([1.0, 2.0, np.nan, 4.0]))
    assert has_nan(pl.Series([1.0, None, 3.0, 4.0]))
    assert has_nan(pl.Series([1.0, None, np.nan, 4.0]))

    # pl DataFrame
    assert not has_nan(pl.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0]}))
    assert has_nan(pl.DataFrame({"A": [1.0, 2.0], "B": [np.nan, 4.0]}))
    assert has_nan(pl.DataFrame({"A": [1.0, None], "B": [3.0, 4.0]}))
    assert has_nan(pl.DataFrame({"A": [1.0, None], "B": [np.nan, 4.0]}))


@enforce_types
def test_fill_nans_pd():
    _test_fill_nans(pd)


@enforce_types
def test_fill_nans_pl():
    _test_fill_nans(pl)


@enforce_types
def _test_fill_nans(pdl):
    # nan at front
    df1 = pdl.DataFrame({"A": [np.nan, 1.0, 2.0, 3.0, 4.0, 5.0]})
    df2 = fill_nans(df1)
    assert not has_nan(df2)

    # nan in middle
    df1 = pdl.DataFrame({"A": [1.0, 2.0, np.nan, 3.0, 4.0]})
    df2 = fill_nans(df1)
    assert not has_nan(df2)

    # nan at end
    df1 = pdl.DataFrame({"A": [1.0, 2.0, 3.0, 4.0, np.nan]})
    df2 = fill_nans(df1)
    assert not has_nan(df2)

    # nan at front, middle, end
    df1 = pdl.DataFrame({"A": [np.nan, 1.0, 2.0, np.nan, 3.0, 4.0, np.nan]})
    df2 = fill_nans(df1)
    assert not has_nan(df2)


@enforce_types
def test_nmse():
    y = np.array([10.0, 12.0, 13.0, 20.0])
    yhat = np.array([9.0, 11.0, 14.0, 21.0])
    ymin, ymax = 10.0, 20.0
    e = nmse(yhat, y, ymin, ymax)
    assert 0.035 <= e <= 0.036


@enforce_types
def test_wei():
    assert Wei(int(1234 * 1e18)).to_eth() == Eth(1234)
    assert Wei(int(12.34 * 1e18)).to_eth() == Eth(12.34)
    assert Wei(int(0.1234 * 1e18)).to_eth() == Eth(0.1234)

    assert Eth(1234).to_wei() == Wei(1234 * 1e18) and type(Eth(1234).to_wei()) == Wei
    assert Eth(12.34).to_wei == Wei(12.34 * 1e18)
    assert Eth(0.1234).to_wei() == Wei(0.1234 * 1e18)

    assert Wei(int(12.34 * 1e18)).str_with_wei() == "12.34 (12340000000000000000 wei)"


@enforce_types
def test_string_to_bytes32_1_short():
    data = "hello"
    data_bytes32 = string_to_bytes32(data)
    assert data_bytes32 == b"hello000000000000000000000000000"


@enforce_types
def test_string_to_bytes32_2_long():
    data = "hello" + "a" * 50
    data_bytes32 = string_to_bytes32(data)
    assert data_bytes32 == b"helloaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@enforce_types
@pytest.mark.parametrize(
    "input_data,expected_output",
    [
        ("short", b"short" + b"0" * 27),
        ("this is exactly 32 chars", b"this is exactly 32 chars00000000"),
        (
            "this is a very long string which is more than 32 chars",
            b"this is a very long string which",
        ),
    ],
)
@enforce_types
def test_string_to_bytes32_3(input_data, expected_output):
    result = string_to_bytes32(input_data)
    assert (
        result == expected_output
    ), f"For {input_data}, expected {expected_output}, but got {result}"
