from datetime import datetime

from freezegun import freeze_time

from pdr_backend.util.time_types import UnixTimeMs, UnixTimeS


# value is in UTC, timezone of system will be -5
@freeze_time("2024-01-01 13:00:00", tz_offset=-5)
def test_time_now_implicit():
    assert datetime.now().isoformat() == "2024-01-01T08:00:00"
    assert datetime.utcnow().isoformat() == "2024-01-01T13:00:00"

    now_ms = UnixTimeMs.now()
    assert int(now_ms) == 1704114000000  # corresponds to 2024-01-01 13:00:00 UTC

    now_s = UnixTimeS.now()
    assert int(now_s) == 1704114000  # corresponds to 2024-01-01 13:00:00 UTC


# needed because it takes a couple of ms to run instructions in the test
def _close_ints(x, y):
    return abs(x - y) <= 2


# can not use freezegun fixtures because it does not work with dateparser
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
