from datetime import datetime, timezone


class UnixTimeSeconds(int):
    def __new__(cls, time_s):
        if time_s < 0 or time_s > 9999999999:
            raise ValueError("Invalid Unix timestamp in seconds")

        return super(UnixTimeSeconds, cls).__new__(cls, time_s)

    def to_milliseconds(self) -> "UnixTimeMilliseconds":
        return UnixTimeMilliseconds(int(self) * 1000)

    @staticmethod
    def now() -> "UnixTimeSeconds":
        return UnixTimeSeconds(int(datetime.now().timestamp()))

    @staticmethod
    def from_dt(from_dt: datetime) -> "UnixTimeSeconds":
        return UnixTimeSeconds(int(from_dt.timestamp()))


class UnixTimeMilliseconds(int):
    def __new__(cls, time_ms):
        if time_ms < 0 or time_ms > 9999999999999:
            raise ValueError("Invalid Unix timestamp in miliseconds")

        return super(UnixTimeMilliseconds, cls).__new__(cls, time_ms)

    def to_seconds(self) -> "UnixTimeSeconds":
        return UnixTimeSeconds(int(self) // 1000)

    @staticmethod
    def now() -> "UnixTimeMilliseconds":
        return UnixTimeMilliseconds(datetime.now().timestamp() * 1000)

    @staticmethod
    def from_dt(from_dt: datetime) -> "UnixTimeMilliseconds":
        return UnixTimeMilliseconds(int(from_dt.timestamp() * 1000))

    @staticmethod
    def from_timestr(timestr: str) -> "UnixTimeMilliseconds":
        if timestr.lower() == "now":
            return UnixTimeMilliseconds.now()

        ncolon = timestr.count(":")
        if ncolon == 0:
            dt = datetime.strptime(timestr, "%Y-%m-%d")
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
        return UnixTimeMilliseconds.from_dt(dt)

    def to_dt(self) -> datetime:
        # precondition
        assert int(self) >= 0, self

        # main work
        dt = datetime.utcfromtimestamp(int(self) / 1000)
        dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone

        # postcondition
        ut2 = int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
        assert ut2 == self, (self, ut2)

        return dt

    def to_timestr(self) -> str:
        dt: datetime.datetime = self.to_dt()

        return dt.strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]

    def pretty_timestr(self) -> str:
        return f"timestamp={self}, dt={self.to_timestr()}"
