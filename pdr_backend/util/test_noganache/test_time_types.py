import datetime
from datetime import timezone

import pytest
from enforce_typing import enforce_types

from pdr_backend.util.time_types import UnixTimeMs, UnixTimeS


@enforce_types
def test_pretty_timestr():
    ut = UnixTimeMs(1648576512345)
    s = ut.pretty_timestr()
    assert "1648576512345" in s  # ut
    assert "2022-03-29" in s  # date
    assert "17:55:12.345" in s  # time with hour, min, s, ms


@enforce_types
def test_current_ut_ms():
    ut = UnixTimeMs.now()
    assert isinstance(ut, UnixTimeMs)
    assert ut > 1648576500000


@enforce_types
def test_from_timestr():
    t = UnixTimeMs.from_timestr("now")
    assert t > 1648576500000 and isinstance(t, int)

    # ensure it returns an int
    assert isinstance(UnixTimeMs.from_timestr("1970-01-01"), int)
    assert isinstance(UnixTimeMs.from_timestr("1970-01-01_0:00:00.123"), int)

    # unix start time (Jan 1 1970), with increasing levels of precision
    assert UnixTimeMs.from_timestr("1970-01-01") == 0
    assert UnixTimeMs.from_timestr("1970-01-01_0:00") == 0
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:00") == 0
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:00.000") == 0

    # shortly after unix start time
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:00.001") == 1
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:00.123") == 123
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:01") == 1000
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:01.000") == 1000
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:01.234") == 1234
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:10.002") == 10002
    assert UnixTimeMs.from_timestr("1970-01-01_0:00:12.345") == 12345

    # modern times
    assert UnixTimeMs.from_timestr("2022-03-29") == 1648512000000
    assert UnixTimeMs.from_timestr("2022-03-29_17:55") == 1648576500000
    assert UnixTimeMs.from_timestr("2022-03-29_17:55:12.345") == 1648576512345

    # test error
    with pytest.raises(ValueError):
        UnixTimeMs.from_timestr("::::::::")


@enforce_types
def test_ut_to_timestr():
    # ensure it returns a str
    assert isinstance(UnixTimeMs(0).to_timestr(), str)
    assert isinstance(UnixTimeMs(1).to_timestr(), str)
    assert isinstance(UnixTimeMs(1648576500000).to_timestr(), str)
    assert isinstance(UnixTimeMs(1648576500001).to_timestr(), str)

    # unix start time (Jan 1 1970), with increasing levels of precision
    assert UnixTimeMs(0).to_timestr() == "1970-01-01_00:00:00.000"
    assert UnixTimeMs(1).to_timestr() == "1970-01-01_00:00:00.001"
    assert UnixTimeMs(123).to_timestr() == "1970-01-01_00:00:00.123"
    assert UnixTimeMs(1000).to_timestr() == "1970-01-01_00:00:01.000"
    assert UnixTimeMs(1234).to_timestr() == "1970-01-01_00:00:01.234"
    assert UnixTimeMs(10002).to_timestr() == "1970-01-01_00:00:10.002"
    assert UnixTimeMs(12345).to_timestr() == "1970-01-01_00:00:12.345"

    # modern times
    assert UnixTimeMs(1648512000000).to_timestr() == "2022-03-29_00:00:00.000"
    assert UnixTimeMs(1648576500000).to_timestr() == "2022-03-29_17:55:00.000"
    assert UnixTimeMs(1648576512345).to_timestr() == "2022-03-29_17:55:12.345"


@enforce_types
def test_ut_to_iso_timestr():
    # ensure it returns a str
    assert isinstance(UnixTimeMs(0).to_iso_timestr(), str)
    assert isinstance(UnixTimeMs(1).to_iso_timestr(), str)
    assert isinstance(UnixTimeMs(1648576500000).to_iso_timestr(), str)
    assert isinstance(UnixTimeMs(1648576500001).to_iso_timestr(), str)

    # unix start time (Jan 1 1970), with increasing levels of precision
    assert UnixTimeMs(0).to_iso_timestr() == "1970-01-01T00:00:00.000Z"
    assert UnixTimeMs(1).to_iso_timestr() == "1970-01-01T00:00:00.001Z"
    assert UnixTimeMs(123).to_iso_timestr() == "1970-01-01T00:00:00.123Z"
    assert UnixTimeMs(1000).to_iso_timestr() == "1970-01-01T00:00:01.000Z"
    assert UnixTimeMs(1234).to_iso_timestr() == "1970-01-01T00:00:01.234Z"
    assert UnixTimeMs(10002).to_iso_timestr() == "1970-01-01T00:00:10.002Z"
    assert UnixTimeMs(12345).to_iso_timestr() == "1970-01-01T00:00:12.345Z"

    # modern times
    assert UnixTimeMs(1648512000000).to_iso_timestr() == "2022-03-29T00:00:00.000Z"
    assert UnixTimeMs(1648576500000).to_iso_timestr() == "2022-03-29T17:55:00.000Z"
    assert UnixTimeMs(1648576512345).to_iso_timestr() == "2022-03-29T17:55:12.345Z"


@enforce_types
def test_dt_to_ut_and_back():
    dt = datetime.datetime.strptime("2022-03-29_17:55", "%Y-%m-%d_%H:%M")
    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone

    ut = UnixTimeMs.from_dt(dt)
    assert ut == UnixTimeMs(1648576500000)

    dt2 = ut.to_dt()
    assert dt2 == dt


@enforce_types
def test_timezones():
    # set targets
    dt = datetime.datetime.now()
    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone
    ut_s_target = dt.timestamp()
    ut_ms_target = ut_s_target * 1000

    # set tolerances
    tol_s = 1
    tol_ms = tol_s * 1000

    # test UnixTimeS
    # - if it's off by 7200, that's 3600 * 2 --> 2 timezones from UTC
    ut_s = UnixTimeS.now()
    assert ut_s == pytest.approx(ut_s_target, abs=tol_s)

    # test UnixTimeMs
    # - if it's off by 7200*1000, that's 3600 * 2 * 1000 --> 2 timezones fr UTC
    ut_ms = UnixTimeMs.now()
    assert ut_ms == pytest.approx(ut_ms_target, abs=tol_ms)
