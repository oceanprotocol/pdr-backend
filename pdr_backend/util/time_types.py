from datetime import datetime, timezone

import dateparser
from enforce_typing import enforce_types


class UnixTimeS(int):
    @enforce_types
    def __new__(cls, time_s):
        if time_s < 0 or time_s > 9999999999:
            raise ValueError("Invalid Unix timestamp in seconds")

        return super(UnixTimeS, cls).__new__(cls, time_s)

    @enforce_types
    def to_milliseconds(self) -> "UnixTimeMs":
        return UnixTimeMs(int(self) * 1000)

    @staticmethod
    def now() -> "UnixTimeS":
        dt = _dt_now_UTC()
        return UnixTimeS(int(dt.timestamp()))

    @staticmethod
    def from_dt(from_dt: datetime) -> "UnixTimeS":
        return UnixTimeS(int(from_dt.timestamp()))


class UnixTimeMs(int):
    @enforce_types
    def __new__(cls, time_ms):
        if time_ms < 0 or time_ms > 9999999999999:
            raise ValueError("Invalid Unix timestamp in miliseconds")

        return super(UnixTimeMs, cls).__new__(cls, time_ms)

    @enforce_types
    def to_seconds(self) -> "UnixTimeS":
        return UnixTimeS(int(self) // 1000)

    @staticmethod
    def now() -> "UnixTimeMs":
        dt = _dt_now_UTC()
        return UnixTimeMs(dt.timestamp() * 1000)

    @staticmethod
    def from_dt(dt: datetime) -> "UnixTimeMs":
        return UnixTimeMs(int(dt.timestamp() * 1000))

    @staticmethod
    def from_natural_language(nat_lang: str) -> "UnixTimeMs":
        dt = dateparser.parse(nat_lang).replace(tzinfo=timezone.utc)
        return UnixTimeMs(dt.timestamp() * 1000)

    @staticmethod
    def from_timestr(timestr: str) -> "UnixTimeMs":
        ncolon = timestr.count(":")
        if ncolon == 0:
            try:
                dt = datetime.strptime(timestr, "%Y-%m-%d")
            except ValueError:
                return UnixTimeMs.from_natural_language(timestr)
        elif ncolon == 1:
            dt = datetime.strptime(timestr, "%Y-%m-%d_%H:%M")
        elif ncolon == 2:
            if "." not in timestr:
                dt = datetime.strptime(timestr, "%Y-%m-%d_%H:%M:%S")
            else:
                dt = datetime.strptime(timestr, "%Y-%m-%d_%H:%M:%S.%f")
        else:
            raise ValueError(timestr)

        dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone
        return UnixTimeMs.from_dt(dt)

    @staticmethod
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
def _dt_now_UTC() -> datetime:
    dt = datetime.now()
    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone
    return dt
