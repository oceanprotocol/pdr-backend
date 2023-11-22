from typing import List

from enforce_typing import enforce_types

from pdr_backend.util.constants import CAND_TIMEFRAMES


@enforce_types
def pack_timeframe_str_list(timeframe_str_list) -> str:
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
