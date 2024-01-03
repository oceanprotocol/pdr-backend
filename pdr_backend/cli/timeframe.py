from typing import List, Union

from enforce_typing import enforce_types

from pdr_backend.util.constants import CAND_TIMEFRAMES


class Timeframe:
    def __init__(self, timeframe_str: str):
        """
        @arguments
          timeframe_str -- e.g. "5m"
        """
        if timeframe_str not in CAND_TIMEFRAMES:
            raise ValueError(timeframe_str)
        self.timeframe_str = timeframe_str

    @property
    def ms(self) -> int:
        """Returns timeframe, in ms"""
        return self.m * 60 * 1000

    @property
    def s(self) -> int:
        """Returns timeframe, in s"""
        return self.m * 60

    @property
    def m(self) -> int:
        """Returns timeframe, in minutes"""
        if self.timeframe_str == "1m":
            return 1
        if self.timeframe_str == "5m":
            return 5
        if self.timeframe_str == "1h":
            return 60
        raise ValueError(f"need to support timeframe={self.timeframe_str}")

    def __str__(self):
        return self.timeframe_str


class Timeframes(List[Timeframe]):
    def __init__(self, timeframes: Union[List[str], List[Timeframe]]):
        if not isinstance(timeframes, list):
            raise TypeError("timeframes must be a list")

        frames = []
        for timeframe in timeframes:
            if isinstance(timeframe, str):
                frame = Timeframe(timeframe)

            frames.append(frame)

        super().__init__(frames)

    @staticmethod
    def from_str(timeframes_str: str):
        """
        @description
          Parses a comma-separated string of timeframes, e.g. "1h,5m"
        """
        if not isinstance(timeframes_str, str):
            raise TypeError("timeframes_strs must be a string")

        return Timeframes(timeframes_str.split(","))

    def __str__(self):
        if not self:
            return ""

        return ",".join([str(frame) for frame in self])


@enforce_types
def s_to_timeframe_str(seconds: int) -> str:
    if seconds == 300:
        return "5m"
    if seconds == 3600:
        return "1h"
    return ""


@enforce_types
def verify_timeframes_str(signal_str: str):
    """
    @description
      Raise an error if signal is invalid.

    @argument
      signal_str -- e.g. "close"
    """
    try:
        Timeframes.from_str(signal_str)
        return True
    except ValueError:
        return False
