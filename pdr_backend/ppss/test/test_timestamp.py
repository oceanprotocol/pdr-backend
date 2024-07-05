#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timedelta, timezone, UTC
from zoneinfo import available_timezones, ZoneInfo

from enforce_typing import enforce_types
import freezegun
import pytest
import time_machine

from pdr_backend.util.time_types import (
    timestr,
    UnixTimeMs,
    UnixTimeS,
)

@enforce_types
def timestr(dt: datetime) -> str:
    """Simple time string, useful for testing"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

@enforce_types
def _tz_offset_from_utc(delta_hours:int):
    """Return a timezone that's offset from UTC by the specified # hours"""
    if delta_hours < 0:
        delta_hours += 24
    utc_dt = datetime(2024, 1, 1, 13, tzinfo=timezone.utc)
    for cand_tz_str in available_timezones():
        cand_tz = ZoneInfo(cand_tz_str)
        cand_dt = datetime(2024, 1, 1, 13, tzinfo=cand_tz)
        cand_delta_hours = (utc_dt - cand_dt).seconds / 3600
        if cand_delta_hours == delta_hours:
            return cand_tz
    raise ValueError("No timezone found with target delta_hours")
TZ_MINUS_5 = _tz_offset_from_utc(-5)

@time_machine.travel(datetime(2024, 1, 1, 8, 0, 0, tzinfo=TZ_MINUS_5))
def test_time_now_implicit():    
    # set targets
    target_utc_minus_5_str = "2024-01-01 08:00:00"
    target_utc_str = "2024-01-01 13:00:00"
    target_utc_ms = 1704114000000
    target_utc_s = 1704114000

    # test: datetime library directly, to confirm time_machine.travel() behavior
    assert timestr(datetime.now(UTC)) == target_utc_str
    assert timestr(datetime.now()) == target_utc_minus_5_str

    # test: UnixTimeMs(utc_ms).to_dt()
    assert timestr(UnixTimeMs(target_utc_ms).to_dt()) == target_utc_str

    # test: time_types.UnixTimeMs. Its now() should always return a value in UTC
    utc_ms = UnixTimeMs.now()
    assert int(utc_ms) == target_utc_ms
    assert timestr(UnixTimeMs(utc_ms).to_dt()) == target_utc_str

    # test: time_types.UnixTimeS. Its now() should always return a value in UTC
    utc_s = UnixTimeS.now()
    assert utc_s == target_utc_s
    assert timestr(UnixTimeMs(utc_s * 1000).to_dt()) == target_utc_str

# We specify that it's 1pm UTC, or 8am UTC-5
# First arg to freeze_time() is in UTC, second arg is how much to offset it by,
#   therefore the computer running this block should see time as utc - 5
# Alas, freezegun can't properly handle timezones, so we shouldn't use it
@freezegun.freeze_time("2024-01-01 13:00:00", tz_offset=-5)
def test_how_freezegun_is_wrong():
    with pytest.raises(AssertionError):
        # freezegun should not treat these as equal
        assert timestr(datetime.now(UTC)) != timestr(datetime.now())

    with pytest.raises(AssertionError):
        # freezegun will think datetime.now(UTC) is 8am, not 1pm
        assert timestr(datetime.now(UTC)) == "2024-01-01 13:00:00"

    # freezegun gets this right, but that's because it's naive wrt timezone
    assert timestr(datetime.now()) == "2024-01-01 08:00:00"

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
