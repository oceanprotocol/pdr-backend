import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.timeframe import Timeframe, Timeframes, s_to_timeframe_str


@enforce_types
def test_timeframe_class_1m():
    t = Timeframe("1m")
    assert t.timeframe_str == "1m"
    assert t.m == 1
    assert t.s == 1 * 60
    assert t.ms == 1 * 60 * 1000


@enforce_types
def test_timeframe_class_5m():
    t = Timeframe("5m")
    assert t.timeframe_str == "5m"
    assert t.m == 5
    assert t.s == 5 * 60
    assert t.ms == 5 * 60 * 1000


@enforce_types
def test_timeframe_class_1h():
    t = Timeframe("1h")
    assert t.timeframe_str == "1h"
    assert t.m == 60
    assert t.s == 60 * 60
    assert t.ms == 60 * 60 * 1000


@enforce_types
def test_timeframe_class_bad():
    with pytest.raises(ValueError):
        Timeframe("foo")

    t = Timeframe("1h")
    # forcefully change the model
    t.timeframe_str = "BAD"

    with pytest.raises(ValueError):
        _ = t.m


@enforce_types
def test_pack_timeframe_str_list():
    assert str(Timeframes([])) == ""
    assert str(Timeframes(["1h"])) == "1h"
    assert str(Timeframes(["1h", "5m"])) == "1h,5m"

    assert str(Timeframes.from_str("1h,5m")) == "1h,5m"

    with pytest.raises(TypeError):
        Timeframes.from_str(None)

    with pytest.raises(TypeError):
        Timeframes("")

    with pytest.raises(TypeError):
        Timeframes(None)

    with pytest.raises(ValueError):
        Timeframes(["adfs"])

    with pytest.raises(ValueError):
        Timeframes(["1h fgds"])


@enforce_types
def test_verify_timeframe_str():
    Timeframe("1h")
    Timeframe("1m")

    with pytest.raises(ValueError):
        Timeframe("foo")


@enforce_types
def test_s_to_timeframe_str():
    assert s_to_timeframe_str(300) == "5m"
    assert s_to_timeframe_str(3600) == "1h"

    assert s_to_timeframe_str(0) == ""
    assert s_to_timeframe_str(100) == ""
    assert s_to_timeframe_str(-300) == ""

    with pytest.raises(TypeError):
        s_to_timeframe_str("300")
