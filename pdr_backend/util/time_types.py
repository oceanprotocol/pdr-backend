from datetime import datetime


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
