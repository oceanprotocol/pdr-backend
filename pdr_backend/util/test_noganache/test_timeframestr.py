from enforce_typing import enforce_types
import pytest

from pdr_backend.util.timeframestr import (
    Timeframe,
    pack_timeframe_str_list,
    verify_timeframe_str,
    s_to_timeframe_str,
)


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


@enforce_types
def test_pack_timeframe_str_list():
    assert pack_timeframe_str_list(None) is None
    assert pack_timeframe_str_list([]) is None
    assert pack_timeframe_str_list(["1h"]) == "1h"
    assert pack_timeframe_str_list(["1h", "5m"]) == "1h,5m"

    with pytest.raises(TypeError):
        pack_timeframe_str_list("")

    with pytest.raises(ValueError):
        pack_timeframe_str_list(["adfs"])

    with pytest.raises(ValueError):
        pack_timeframe_str_list(["1h fgds"])


@enforce_types
def test_verify_timeframe_str():
    verify_timeframe_str("1h")
    verify_timeframe_str("1m")

    with pytest.raises(ValueError):
        verify_timeframe_str("foo")


@enforce_types
def test_s_to_timeframe_str():
    assert s_to_timeframe_str(300) == "5m"
    assert s_to_timeframe_str(3600) == "1h"

    assert s_to_timeframe_str(0) == ""
    assert s_to_timeframe_str(100) == ""
    assert s_to_timeframe_str(-300) == ""

    with pytest.raises(TypeError):
        s_to_timeframe_str("300")
