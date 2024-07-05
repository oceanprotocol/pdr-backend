#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timezone, UTC
from zoneinfo import available_timezones, ZoneInfo

from enforce_typing import enforce_types


@enforce_types
def tz_offset_from_utc(delta_hours: int):
    """
    Return a timezone that's offset from UTC by the specified # hours.
    This is meant to be used for testing only.
    """
    # preconditions
    assert -24 <= delta_hours <= 24

    # condition input
    if delta_hours < 0:
        delta_hours += 24

    # corner case - guarantee UTC timezone offset is zero
    # (since there are other timezones with offset of zero)
    if delta_hours == 0:
        return UTC

    # We use an arbitrary time: Jan 1, 2024 at 13.00.
    # That's ok because we are looking at the difference between
    # the times, based on two different time zones.
    yyyy, hh, mm, dd = 2024, 1, 1, 13
    utc_dt = datetime(yyyy, hh, mm, dd, tzinfo=timezone.utc)
    for cand_tz_str in sorted(available_timezones()):
        cand_tz = ZoneInfo(cand_tz_str)
        cand_dt = datetime(yyyy, hh, mm, dd, tzinfo=cand_tz)
        cand_delta_hours = (utc_dt - cand_dt).seconds / 3600
        if cand_delta_hours == delta_hours:
            return cand_tz

    raise AssertionError(f"No timezone found for delta_hours={delta_hours}")
