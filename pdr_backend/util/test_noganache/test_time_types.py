#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timedelta, timezone, UTC
from zoneinfo import ZoneInfo

from enforce_typing import enforce_types
import pytest
from pytest import approx
import time_machine

from pdr_backend.util.test_noganache.test_time_types_util import (
    tz_offset_from_utc,
)
from pdr_backend.util.time_types import (
    dt_now_UTC,
    UnixTimeMs,
    UnixTimeS,
)

TZ_UTC_MINUS_5 = tz_offset_from_utc(-5)


@enforce_types
def _simplestr(dt: datetime) -> str:
    """Simple time string, useful for testing"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


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
def test_from_natural_language__now():
    now_ms1 = dt_now_UTC().timestamp() * 1000
    now_ms2 = UnixTimeMs.from_natural_language("now")
    assert isinstance(now_ms2, int)
    assert now_ms1 == approx(now_ms2, abs=1000)


@enforce_types
def test_from_natural_language__2_days_ago():
    def _get_time_n_days_ago(num_days: int) -> int:
        ago_dt = dt_now_UTC() - timedelta(days=num_days)
        ago_ms = int(ago_dt.timestamp() * 1000)
        return ago_ms

    ago_ms1 = _get_time_n_days_ago(num_days=2)
    ago_ms2 = UnixTimeMs.from_natural_language("2 days ago")
    assert isinstance(ago_ms2, int)
    assert ago_ms1 == approx(ago_ms2, abs=1000)


@enforce_types
def test_from_natural_language__unhappy_path():
    with pytest.raises(ValueError):
        UnixTimeMs.from_natural_language("::::::::")


@enforce_types
def test_from_iso_timestr():
    t_iso_str = "2024-04-16T03:35:00.000Z"
    t_UnixTimeMs = UnixTimeMs.from_iso_timestr(t_iso_str)
    assert t_iso_str == t_UnixTimeMs.to_iso_timestr()
    assert t_UnixTimeMs == 1713238500000


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
    dt = datetime.strptime("2022-03-29_17:55", "%Y-%m-%d_%H:%M")
    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone

    ut = UnixTimeMs.from_dt(dt)
    assert ut == UnixTimeMs(1648576500000)

    dt2 = ut.to_dt()
    assert dt2 == dt


@enforce_types
def test_timezones():
    # set targets
    dt = datetime.now(UTC)
    ut_s_target = dt.timestamp()
    ut_ms_target = ut_s_target * 1000

    # set tolerances
    tol_s = 1
    tol_ms = tol_s * 1000

    # test UnixTimeS
    # - if it's off by 7200, that's 3600 * 2 --> 2 timezones from UTC
    ut_s = UnixTimeS.now()
    assert ut_s == approx(ut_s_target, abs=tol_s)

    # test UnixTimeMs
    # - if it's off by 7200*1000, that's 3600 * 2 * 1000 --> 2 timezones fr UTC
    ut_ms = UnixTimeMs.now()
    assert ut_ms == approx(ut_ms_target, abs=tol_ms)


@enforce_types
def testtz_offset_from_utc():
    assert tz_offset_from_utc(0) == UTC

    assert tz_offset_from_utc(-5) == ZoneInfo(key="America/Atikokan")
    assert tz_offset_from_utc(11) == ZoneInfo(key="Antarctica/Macquarie")

    with pytest.raises(AssertionError):
        tz_offset_from_utc(-25)

    with pytest.raises(AssertionError):
        tz_offset_from_utc(+25)


@enforce_types
@time_machine.travel(datetime(2024, 1, 1, 8, 0, 0, tzinfo=TZ_UTC_MINUS_5))
def test_time_now_implicit():
    # set targets
    target_utc_minus_5_str = "2024-01-01 08:00:00"
    target_utc_str = "2024-01-01 13:00:00"
    target_utc_ms = 1704114000000
    target_utc_s = 1704114000

    # test: datetime library directly, to confirm time_machine.travel() behavior
    assert _simplestr(datetime.now(UTC)) == target_utc_str
    assert _simplestr(datetime.now()) == target_utc_minus_5_str

    # test: UnixTimeMs(utc_ms).to_dt()
    assert _simplestr(UnixTimeMs(target_utc_ms).to_dt()) == target_utc_str

    # test: time_types.UnixTimeMs. Its now() should always return a value in UTC
    utc_ms = UnixTimeMs.now()
    assert int(utc_ms) == target_utc_ms
    assert _simplestr(UnixTimeMs(utc_ms).to_dt()) == target_utc_str

    # test: time_types.UnixTimeS. Its now() should always return a value in UTC
    utc_s = UnixTimeS.now()
    assert utc_s == target_utc_s
    assert _simplestr(UnixTimeMs(utc_s * 1000).to_dt()) == target_utc_str


# needed because it takes a few ms to run instructions in the test
def _close_ints(x, y):
    return abs(x - y) <= 20


@enforce_types
def test_time_now_natural_language():
    assert _close_ints(int(UnixTimeMs.from_timestr("now")), int(UnixTimeMs.now()))
    assert _close_ints(
        int(UnixTimeMs.from_timestr("an hour ago")), int(UnixTimeMs.now()) - 3600000
    )
    assert _close_ints(
        int(UnixTimeMs.from_timestr("in one hour")), int(UnixTimeMs.now()) + 3600000
    )

    assert _close_ints(
        int(UnixTimeMs.from_timestr("18 days ago")),
        int(UnixTimeMs.now()) - 3600000 * 24 * 18,
    )


@enforce_types
def test_dt_now_UTC_1():
    dt1 = dt_now_UTC()
    dt2 = datetime.now(UTC)
    assert (dt2 - dt1).seconds < 1
    assert 23.99 < (dt1 - dt2).seconds / 3600 < 23.999999  # fyi, diff wraps around


@enforce_types
@time_machine.travel(datetime(2024, 1, 1, 8, 0, 0, tzinfo=TZ_UTC_MINUS_5))
def test_dt_now_UTC_2():
    dt1 = dt_now_UTC()
    dt2 = datetime.now(UTC)
    assert (dt2 - dt1).seconds < 1
