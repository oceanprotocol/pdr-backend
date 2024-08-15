#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Union

from enforce_typing import enforce_types

from pdr_backend.util.constants import CAND_TIMEFRAMES


# don't use @enforce_types, causes problems
class ArgTimeframe:
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
        return int(self.m * 60 * 1000)

    @property
    def s(self) -> int:
        """Returns timeframe, in s"""
        return int(self.m * 60)

    @property
    def m(self) -> float:
        """Returns timeframe, in minutes"""
        if self.timeframe_str == "1s":
            return 1 / 60
        if self.timeframe_str == "30s":
            return 1 / 2
        if self.timeframe_str == "1m":
            return 1
        if self.timeframe_str == "5m":
            return 5
        if self.timeframe_str == "15m":
            return 15
        if self.timeframe_str == "1h":
            return 60
        raise ValueError(f"need to support timeframe={self.timeframe_str}")

    def __eq__(self, other):
        return self.timeframe_str == str(other)

    def __str__(self):
        return self.timeframe_str


# don't use @enforce_types, causes problems
class ArgTimeframes(List[ArgTimeframe]):
    def __init__(self, timeframes: Union[List[str], List[ArgTimeframe]]):
        if not isinstance(timeframes, list):
            raise TypeError("timeframes must be a list")

        frames = []
        for timeframe in timeframes:
            frame = ArgTimeframe(timeframe) if isinstance(timeframe, str) else timeframe
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

        return ArgTimeframes(timeframes_str.split(","))

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
def verify_timeframe_str(timeframe_str: str):
    """Raise an error if input string is invalid."""
    _ = ArgTimeframe(timeframe_str)


@enforce_types
def verify_timeframes_str(timeframes_str: str):
    """Raise an error if input string is invalid."""
    _ = ArgTimeframes.from_str(timeframes_str)


@enforce_types
def timeframes_str_ok(timeframes_str: str) -> bool:
    """Return True if input string is valid"""
    try:
        ArgTimeframes.from_str(timeframes_str)
        return True
    except ValueError:
        return False
