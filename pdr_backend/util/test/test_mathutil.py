from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import pytest

from pdr_backend.util.mathutil import (
    isNumber,
    intInStr,
    Range,
    randunif,
    round_sig,
    has_nan,
    fill_nans,
    nmse,
)


@enforce_types
def testIsNumber():
    for x in [-2, 0, 2, 20000, -2.1, -2.0, 0.0, 2.0, 2.1, 2e6]:
        assert isNumber(x)

    for x in [[], [1, 2], {}, {1: 2, 2: 3}, None, "", "foo"]:
        assert not isNumber(x)


@enforce_types
def testIntInStr():
    assert intInStr("123") == 123
    assert intInStr("sdds12") == 12
    assert intInStr("sdds12afdsf3zz") == 123
    assert intInStr("sdds12afdsf39sf#@#@9fdsj!!49sd") == 1239949

    assert intInStr("34.56") == 3456
    assert intInStr("0.00006") == 6
    assert intInStr("10.00006") == 1000006

    with pytest.raises(ValueError):
        intInStr("")
    for v in [32, None, {}, []]:
        with pytest.raises(TypeError):
            intInStr(v)


@enforce_types
def testRange():
    r = Range(2.2)
    p = r.drawRandomPoint()
    assert p == 2.2

    r = Range(-1.5, 2.5)
    for _ in range(20):
        p = r.drawRandomPoint()
        assert -1.5 <= p <= 2.5

    r = Range(2.3, None)
    p = r.drawRandomPoint()
    assert p == 2.3

    r = Range(2.3, 2.3)
    p = r.drawRandomPoint()
    assert p == 2.3

    with pytest.raises(AssertionError):
        Range(3.0, 1.0)

    with pytest.raises(TypeError):
        Range(3)
    with pytest.raises(TypeError):
        Range("foo")
    with pytest.raises(TypeError):
        Range(3.0, "foo")


@enforce_types
def testRangeStr():
    r = Range(2.2)
    s = str(r)
    assert "Range={" in s
    assert "min_" in s
    assert "2.2" in s
    assert "Range}" in s


@enforce_types
def testRandunif():
    for _ in range(20):
        # happy path
        p = randunif(-1.5, 2.5)
        assert -1.5 <= p <= 2.5

        p = randunif(-1.5, -0.5)
        assert -1.5 <= p <= -0.5

        p = randunif(0.0, 100.0)
        assert 0.0 <= p <= 100.0

        # min = max
        p = randunif(-2.0, -2.0)
        assert p == -2.0

        p = randunif(0.0, 0.0)
        assert p == 0.0

        p = randunif(2.0, 2.0)
        assert p == 2.0

    # exceptions
    with pytest.raises(AssertionError):
        p = randunif(0.0, -1.0)

    with pytest.raises(TypeError):
        randunif(0.0, 3)
    with pytest.raises(TypeError):
        randunif(0, 3.0)
    with pytest.raises(TypeError):
        randunif(3.0, "foo")


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
def test_has_nan():
    # 1d array
    assert not has_nan(np.array([1.0, 2.0, 3.0, 4.0]))
    assert has_nan(np.array([1.0, 2.0, np.nan, 4.0]))

    # 2d array
    assert not has_nan(np.array([[1.0, 2.0], [3.0, 4.0]]))
    assert has_nan(np.array([[1.0, 2.0], [np.nan, 4.0]]))

    # pd Series
    assert not has_nan(pd.Series([1.0, 2.0, 3.0, 4.0]))
    assert has_nan(pd.Series([1.0, 2.0, np.nan, 4.0]))

    # pd DataFrame
    assert not has_nan(pd.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0]}))
    assert has_nan(pd.DataFrame({"A": [1.0, 2.0], "B": [np.nan, 4.0]}))


@enforce_types
def test_fill_nans():
    # nan at front
    df1 = pd.DataFrame({"A": [np.nan, 1.0, 2.0, 3.0, 4.0, 5.0]})
    df2 = fill_nans(df1)
    assert not has_nan(df2)

    # nan in middle
    df1 = pd.DataFrame({"A": [1.0, 2.0, np.nan, 3.0, 4.0]})
    df2 = fill_nans(df1)
    assert not has_nan(df2)

    # nan at end
    df1 = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0, np.nan]})
    df2 = fill_nans(df1)
    assert not has_nan(df2)

    # nan at front, middle, end
    df1 = pd.DataFrame({"A": [np.nan, 1.0, 2.0, np.nan, 3.0, 4.0, np.nan]})
    df2 = fill_nans(df1)
    assert not has_nan(df2)


@enforce_types
def test_nmse():
    y = np.array([10.0, 12.0, 13.0, 20.0])
    yhat = np.array([9.0, 11.0, 14.0, 21.0])
    ymin, ymax = 10.0, 20.0
    e = nmse(yhat, y, ymin, ymax)
    assert 0.035 <= e <= 0.036
