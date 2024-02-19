import datetime
from datetime import timezone

import pytest
from enforce_typing import enforce_types

from pdr_backend.util.timeutil import (
    current_ut_ms,
    dt_to_ut,
    ms_to_seconds,
    pretty_timestr,
    timestr_to_ut,
    ut_to_dt,
    ut_to_timestr,
)
from pdr_backend.util.time_types import UnixTimeMilliseconds


@enforce_types
def test_pretty_timestr():
    ut = UnixTimeMilliseconds(1648576512345)
    s = pretty_timestr(ut)
    assert "1648576512345" in s  # ut
    assert "2022-03-29" in s  # date
    assert "17:55:12.345" in s  # time with hour, min, s, ms


@enforce_types
def test_current_ut_ms():
    ut = current_ut_ms()
    assert isinstance(ut, UnixTimeMilliseconds)
    assert ut > 1648576500000


@enforce_types
def test_timestr_to_ut():
    t = timestr_to_ut("now")
    assert t > 1648576500000 and isinstance(t, int)

    # ensure it returns an int
    assert isinstance(timestr_to_ut("1970-01-01"), int)
    assert isinstance(timestr_to_ut("1970-01-01_0:00:00.123"), int)

    # unix start time (Jan 1 1970), with increasing levels of precision
    assert timestr_to_ut("1970-01-01") == 0
    assert timestr_to_ut("1970-01-01_0:00") == 0
    assert timestr_to_ut("1970-01-01_0:00:00") == 0
    assert timestr_to_ut("1970-01-01_0:00:00.000") == 0

    # shortly after unix start time
    assert timestr_to_ut("1970-01-01_0:00:00.001") == 1
    assert timestr_to_ut("1970-01-01_0:00:00.123") == 123
    assert timestr_to_ut("1970-01-01_0:00:01") == 1000
    assert timestr_to_ut("1970-01-01_0:00:01.000") == 1000
    assert timestr_to_ut("1970-01-01_0:00:01.234") == 1234
    assert timestr_to_ut("1970-01-01_0:00:10.002") == 10002
    assert timestr_to_ut("1970-01-01_0:00:12.345") == 12345

    # modern times
    assert timestr_to_ut("2022-03-29") == 1648512000000
    assert timestr_to_ut("2022-03-29_17:55") == 1648576500000
    assert timestr_to_ut("2022-03-29_17:55:12.345") == 1648576512345

    # test error
    with pytest.raises(ValueError):
        timestr_to_ut("::::::::")


@enforce_types
def test_ut_to_timestr():
    # ensure it returns a str
    assert isinstance(ut_to_timestr(UnixTimeMilliseconds(0)), str)
    assert isinstance(ut_to_timestr(UnixTimeMilliseconds(1)), str)
    assert isinstance(ut_to_timestr(UnixTimeMilliseconds(1648576500000)), str)
    assert isinstance(ut_to_timestr(UnixTimeMilliseconds(1648576500001)), str)

    # unix start time (Jan 1 1970), with increasing levels of precision
    assert ut_to_timestr(UnixTimeMilliseconds(0)) == "1970-01-01_00:00:00.000"
    assert ut_to_timestr(UnixTimeMilliseconds(1)) == "1970-01-01_00:00:00.001"
    assert ut_to_timestr(UnixTimeMilliseconds(123)) == "1970-01-01_00:00:00.123"
    assert ut_to_timestr(UnixTimeMilliseconds(1000)) == "1970-01-01_00:00:01.000"
    assert ut_to_timestr(UnixTimeMilliseconds(1234)) == "1970-01-01_00:00:01.234"
    assert ut_to_timestr(UnixTimeMilliseconds(10002)) == "1970-01-01_00:00:10.002"
    assert ut_to_timestr(UnixTimeMilliseconds(12345)) == "1970-01-01_00:00:12.345"

    # modern times
    assert (
        ut_to_timestr(UnixTimeMilliseconds(1648512000000)) == "2022-03-29_00:00:00.000"
    )
    assert (
        ut_to_timestr(UnixTimeMilliseconds(1648576500000)) == "2022-03-29_17:55:00.000"
    )
    assert (
        ut_to_timestr(UnixTimeMilliseconds(1648576512345)) == "2022-03-29_17:55:12.345"
    )


@enforce_types
def test_dt_to_ut_and_back():
    dt = datetime.datetime.strptime("2022-03-29_17:55", "%Y-%m-%d_%H:%M")
    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone

    ut = dt_to_ut(dt)
    assert ut == UnixTimeMilliseconds(1648576500000)

    dt2 = ut_to_dt(ut)
    assert dt2 == dt

    with pytest.raises(TypeError):
        ut_to_dt(-1)


@enforce_types
def test_ms_to_seconds():
    seconds = ms_to_seconds(1648576500000)
    assert seconds == 1648576500
