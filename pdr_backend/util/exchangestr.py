from typing import Union

import ccxt
from enforce_typing import enforce_types


@enforce_types
def pack_exchange_str_list(exchange_str_list) -> Union[str, None]:
    """
    Example: Given ["binance","kraken"]
    Return "binance,kraken"
    """
    if exchange_str_list in [None, []]:
        return None
    if not isinstance(exchange_str_list, list):
        raise TypeError(exchange_str_list)
    for exchange_str in exchange_str_list:
        verify_exchange_str(exchange_str)

    exchanges_str = ",".join(exchange_str_list)
    return exchanges_str


@enforce_types
def verify_exchange_str(exchange_str: str):
    """
    @description
      Raise an error if exchange is invalid.

    @argument
      exchange_str -- e.g. "binance"
    """
    # it's valid if ccxt sees it
    if not hasattr(ccxt, exchange_str):
        raise ValueError(exchange_str)
