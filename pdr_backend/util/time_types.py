#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timezone, UTC
from typing import Union
from zoneinfo import available_timezones, ZoneInfo

import dateparser
from enforce_typing import enforce_types
from numpy import int64


class UnixTimeS(int):
    @enforce_types
    def __new__(cls, time_s: Union[int, int64]) -> "UnixTimeS":
        if time_s < 0 or time_s > 9_999_999_999:
            raise ValueError("Invalid Unix timestamp in seconds")

        return super(UnixTimeS, cls).__new__(cls, time_s)

    @enforce_types
    def to_milliseconds(self) -> "UnixTimeMs":
        return UnixTimeMs(int(self) * 1000)

    @staticmethod
    @enforce_types
    def now() -> "UnixTimeS":
        dt = dt_now_UTC()
        return UnixTimeS(int(dt.timestamp()))

    @staticmethod
    @enforce_types
    def from_dt(from_dt: datetime) -> "UnixTimeS":
        return UnixTimeS(int(from_dt.timestamp()))

    @enforce_types
    def to_dt(self) -> datetime:
        # precondition
        assert int(self) >= 0, self

        # main work
        dt = datetime.fromtimestamp(int(self), timezone.utc)
        dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone

        # postcondition
        ut2 = int(dt.timestamp())
        assert ut2 == self, (self, ut2)

        return dt


class UnixTimeMs(int):
    @enforce_types
    def __new__(cls, time_ms: Union[int, int64]) -> "UnixTimeMs":
        if time_ms < 0 or time_ms > 9_999_999_999_999:
            raise ValueError("Invalid Unix timestamp in miliseconds")

        return super(UnixTimeMs, cls).__new__(cls, time_ms)

    @enforce_types
    def to_seconds(self) -> "UnixTimeS":
        return UnixTimeS(int(self) // 1000)

    @staticmethod
    @enforce_types
    def now() -> "UnixTimeMs":
        dt = dt_now_UTC()
        return UnixTimeMs(int(dt.timestamp() * 1000))

    @staticmethod
    @enforce_types
    def from_dt(dt: datetime) -> "UnixTimeMs":
        return UnixTimeMs(int(dt.timestamp() * 1000))

    @staticmethod
    @enforce_types
    def from_natural_language(nat_lang: str) -> "UnixTimeMs":
        try:
            dt = dateparser.parse(nat_lang, settings={"RETURN_AS_TIMEZONE_AWARE": True})
            dt = dt.astimezone(timezone.utc)

            return UnixTimeMs.from_dt(dt)
        except AttributeError as e:
            raise ValueError(f"Could not parse {nat_lang}.") from e

    @staticmethod
    @enforce_types
    def from_timestr(time_str: str) -> "UnixTimeMs":
        ncolon = time_str.count(":")
        if ncolon == 0:
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d")
            except ValueError:
                return UnixTimeMs.from_natural_language(time_str)
        elif ncolon == 1:
            dt = datetime.strptime(time_str, "%Y-%m-%d_%H:%M")
        elif ncolon == 2:
            if "." not in time_str:
                dt = datetime.strptime(time_str, "%Y-%m-%d_%H:%M:%S")
            else:
                dt = datetime.strptime(time_str, "%Y-%m-%d_%H:%M:%S.%f")
        else:
            raise ValueError(time_str)

        dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone
        return UnixTimeMs.from_dt(dt)

    @staticmethod
    @enforce_types
    def from_iso_timestr(iso_timestr: str) -> "UnixTimeMs":
        """Example iso_timestr: '2024-04-16T03:35:00.000Z'"""
        dt = datetime.strptime(iso_timestr, "%Y-%m-%dT%H:%M:%S.%fZ")
        dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone
        return UnixTimeMs.from_dt(dt)

    @enforce_types
    def to_dt(self) -> datetime:
        # precondition
        assert int(self) >= 0, self

        # main work
        dt = datetime.fromtimestamp(int(self) / 1000, timezone.utc)
        dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone

        # postcondition
        ut2 = int(dt.timestamp() * 1000)
        assert ut2 == self, (self, ut2)

        return dt

    @enforce_types
    def to_timestr(self) -> str:
        dt: datetime = self.to_dt()

        return dt.strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]

    @enforce_types
    def to_iso_timestr(self) -> str:
        dt: datetime = self.to_dt()

        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"  # tack on timezone

    @enforce_types
    def pretty_timestr(self) -> str:
        return f"timestamp={self}, dt={self.to_timestr()}"


@enforce_types
def _tz_offset_from_utc(delta_hours: int):
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


@enforce_types
def dt_now_UTC() -> datetime:
    """Returns the time now, with a guarantee that it's UTC timezone"""
    return datetime.now(UTC)
