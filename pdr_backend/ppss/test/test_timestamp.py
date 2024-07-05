#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timezone, timedelta

import time_machine
import freezegun

from pdr_backend.util.time_types import UnixTimeMs, UnixTimeS

TIMEZONE_UTC = timezone.utc
FREEZE_TIME_UTC = datetime(2024, 1, 1, 13, 0, 0, tzinfo=TIMEZONE_UTC)

TIMEZONE_UTC_MINUS_5 = timezone(-timedelta(hours=5))
#FREEZE_TIME_UTC_MINUS_5 = datetime(2024, 1, 1, 13-5, 0, 0, tzinfo=TIMEZONE_UTC_MINUS_5)
FREEZE_TIME_UTC_MINUS_5 = datetime(2024, 1, 1, 13-5, 0, 0, tzinfo=TIMEZONE_UTC_MINUS_5)

# Issue: freezegun FakeDatetime timestamps don't match those generated from real datetime in some instances
# Solution: bypass it by setting the timezone of the frozen timestamp to utc, hence testing in UTC instead of local time
# https://github.com/spulec/freezegun/issues/346

#@freezegun.freeze_time(time_to_freeze=FREEZE_TIME_UTC_MINUS_5) # specify time incl timezone info; don't specify railgun timezone so it's implicitly utc
#
#@freezegun.freeze_time(time_to_freeze=FREEZE_TIME_UTC_MINUS_5, tz_offset=-5) # specify time incl timezone info; do specify railgun timezone too 
#
#@freezegun.freeze_time("2024-01-01 13:00:00", tz_offset=-5) # specify time w/o timezone info; do specify railgun timezone too 
# first arg to freeze_time() is in UTC, second arg is how much to offset it by,
#   therefore the computer running this block will see time as utc - 5

# problem: travel.__init__() got an unexpected keyword argument 'tz_offset'
# @time_machine.travel("2024-01-01 13:00:00", tz_offset=-5)

# problem: it implicitly stays in UTC timezone
#@time_machine.travel(FREEZE_TIME_UTC_MINUS_5)

from zoneinfo import ZoneInfo, available_timezones
# dt1 = datetime(2024, 1, 1, 13, tzinfo=timezone.utc)
# dt2 = datetime(2024, 1, 1, 13, tzinfo=ZoneInfo("America/New_York"))
# delta_hours = (dt2 - dt1).seconds/3600
# tz_minus_five = None
# for cand_tz_str in available_timezones():
#     cand_tz = ZoneInfo(cand_tz_str)
#     dt3 = datetime(2024, 1, 1, 13, tzinfo=cand_tz)
#     cand_delta_hours = (dt3 - dt1).seconds/3600
#     if cand_delta_hours == -5:
#         tz_minus_five = cand_tz
#         break
# import pdb; pdb.set_trace()
# hill_valley_tz = ZoneInfo("America/Los_Angeles")
# @time_machine.travel(datetime(2024, 1, 1, 13-0, 0, 0, tzinfo=hill_valley_tz))

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

def _timestr(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") 

@time_machine.travel(datetime(2024, 1, 1, 8, 0, 0, tzinfo=TZ_MINUS_5))
def test_time_now_implicit():    
    # set targets
    target_utc_minus_5_str = "2024-01-01 08:00:00"

    target_utc_str = "2024-01-01 13:00:00"
    target_utc_ms = 1704114000000
    target_utc_s = 1704114000

    # test: datetime library directly, to confirm time_machine.travel() behavior
    assert _timestr(datetime.utcnow()) == target_utc_str
    assert _timestr(datetime.now()) == target_utc_minus_5_str

    # test: UnixTimeMs(utc_ms).to_dt()
    assert _timestr(UnixTimeMs(target_utc_ms).to_dt()) == target_utc_str

    # test: time_types.UnixTimeMs. Its now() should always return a value in UTC
    utc_ms = UnixTimeMs.now()
    assert int(utc_ms) == target_utc_ms
    assert _timestr(UnixTimeMs(utc_ms).to_dt()) == target_utc_str

    # test: time_types.UnixTimeS. Its now() should always return a value in UTC
    utc_s = UnixTimeS.now()
    assert utc_s == target_utc_s
    assert _timestr(UnixTimeMs(utc_s * 1000).to_dt()) == target_utc_str


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
