from os import getenv
import sys
from typing import List, Union

from enforce_typing import enforce_types

@enforce_types
def getenv_or_exit(envvar_name: str) -> Union[None, str]:
    value = getenv(envvar_name)
    if value is None:
        print(f"You must set {envvar_name} environment variable")
        sys.exit(1)
    return value

@enforce_types
def parse_filters() -> List[Union[List[str],None]]:
    """
    @description
      Grabs envvar values for each of the filters (PAIR_FILTER, etc).
      Then, parses each: splits the string into a list.
      Returns the list.

    @arguments
      <nothing, but it grabs from env>

    @return
      filter_values -- list with one item per filter:
        0. parsed PAIR_FILTER -- either [pair1_str, pair2_str, ..] or None
        1. parsed TIMEFRAME_FILTER -- ""
        ...
    """
    filter_names = [
        "PAIR_FILTER",
        "TIMEFRAME_FILTER",
        "SOURCE_FILTER",
        "OWNER_ADDRS"
    ]
    filter_values = [
        getenv(name).split(",")
        if getenv(name) else None
        for name in filter_names
    ]
    return filter_values
