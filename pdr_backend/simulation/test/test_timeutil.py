import datetime
from datetime import timezone

from enforce_typing import enforce_types

from pdr_backend.simulation.timeutil import (
    pretty_timestr,
    current_ut,
    dt_to_ut,
    ut_to_dt,
    timestr_to_ut,
    ms_to_seconds,
)


@enforce_types
def test_pretty_timestr():
    ut = 1648576500000
    s = pretty_timestr(ut)
    assert "1648576500000" in s  # ut
    assert "2022-03-29" in s  # date
    assert "17:55" in s  # time


@enforce_types
def test_current_ut():
    ut = current_ut()
    assert isinstance(ut, int)
    assert ut > 1648576500000


@enforce_types
def test_timestr_to_ut():
    t = timestr_to_ut("now")
    assert t > 1648576500000 and isinstance(t, int)

    t = timestr_to_ut("1970-01-01_0:00")
    assert t == 0 and isinstance(t, int)

    t = timestr_to_ut("2022-03-29_17:55")
    assert t == 1648576500000 and isinstance(t, int)

    t = timestr_to_ut("2022-03-29")
    assert t == 1648512000000 and isinstance(t, int)


@enforce_types
def test_dt_to_ut_and_back():
    dt = datetime.datetime.strptime("2022-03-29_17:55", "%Y-%m-%d_%H:%M")
    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone

    ut = dt_to_ut(dt)
    assert ut == 1648576500000

    dt2 = ut_to_dt(ut)
    assert dt2 == dt


@enforce_types
def test_ms_to_seconds():
    seconds = ms_to_seconds(1648576500000)
    assert seconds == 1648576500
