from os import getenv
import sys
from typing import List, Tuple, Union

from enforce_typing import enforce_types


@enforce_types
def getenv_or_exit(envvar_name: str) -> Union[None, str]:
    value = getenv(envvar_name)
    if value is None:
        print(f"You must set {envvar_name} environment variable")
        sys.exit(1)
    return value


@enforce_types
def parse_filters() -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    @description
      Grabs envvar values for each of the filters (PAIR_FILTER, etc).
      Then, parses each: splits the string into a list.
      Returns the list.

    @arguments
      <nothing, but it grabs from env>

    @return
      parsed_pair_filter -- e.g. [] or ["ETH-USDT", "BTC-USDT"]
      parsed_timeframe_filter -- e.g. ["5m"]
      parsed_source_filter -- e.g. ["binance"]
      parsed_owner_addrs -- e.g. ["0x123.."]

    @notes
      if envvar is None, the parsed filter is [], *not* None
    """

    def _parse1(envvar) -> List[str]:
        envval = getenv(envvar)
        if envval is None:
            return []
        return envval.split(",")

    return (
        _parse1("PAIR_FILTER"),
        _parse1("TIMEFRAME_FILTER"),
        _parse1("SOURCE_FILTER"),
        _parse1("OWNER_ADDRS"),
    )
