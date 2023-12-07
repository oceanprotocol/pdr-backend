from typing import Union

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
        if self.timeframe_str == "5m":
            return 5
        if self.timeframe_str == "1h":
            return 60
        raise ValueError("need to support timeframe={self.timeframe_str}")


@enforce_types
def pack_timeframe_str_list(timeframe_str_list) -> Union[str, None]:
    """
    Example: Given ["1m","1h"]
    Return "1m,1h"
    """
    if timeframe_str_list in [None, []]:
        return None
    if not isinstance(timeframe_str_list, list):
        raise TypeError(timeframe_str_list)
    for timeframe_str in timeframe_str_list:
        verify_timeframe_str(timeframe_str)

    timeframes_str = ",".join(timeframe_str_list)
    return timeframes_str


@enforce_types
def verify_timeframe_str(timeframe_str: str):
    """Raises an error if timeframe_str is not e.g. '1m', '1h'."""
    if timeframe_str not in CAND_TIMEFRAMES:
        raise ValueError(timeframe_str)
