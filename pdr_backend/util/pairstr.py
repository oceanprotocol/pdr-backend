import re
from typing import List, Tuple

from enforce_typing import enforce_types

from pdr_backend.util.constants import CAND_USDCOINS


# ==========================================================================
# unpack..() functions


@enforce_types
def unpack_pairs_str(pairs_str: str, do_verify: bool = True) -> List[str]:
    """
    @description
      Unpack the string for *one or more* pairs, into list of pair_str

      Example: Given 'ADA-USDT, BTC/USDT, ETH/USDT'
      Return ['ADA-USDT', 'BTC-USDT', 'ETH-USDT']

    @argument
      pairs_str - '<base>/<quote>' or 'base-quote'
      do_verify - typically T. Only F to avoid recursion from verify functions

    @return
      pair_str_list -- List[<pair_str>]
    """
    pairs_str = pairs_str.strip()
    pairs_str = " ".join(pairs_str.split())  # replace multiple whitespace w/ 1
    pairs_str = pairs_str.replace(", ", ",").replace(" ,", ",")
    pairs_str = pairs_str.replace(" ", ",")
    pairs_str = pairs_str.replace("/", "-")  # ETH/USDT -> ETH-USDT. Safer files.
    pair_str_list = pairs_str.split(",")

    if do_verify:
        if not pair_str_list:
            raise ValueError(pairs_str)

        for pair_str in pair_str_list:
            verify_pair_str(pair_str)

    return pair_str_list


@enforce_types
def unpack_pair_str(pair_str: str, do_verify: bool = True) -> Tuple[str, str]:
    """
    @description
      Unpack the string for a *single* pair, into base_str and quote_str.

      Example: Given 'BTC/USDT' or 'BTC-USDT'
      Return ('BTC', 'USDT')

    @argument
      pair_str - '<base>/<quote>' or 'base-quote'
      do_verify - typically T. Only F to avoid recursion from verify functions

    @return
      base_str -- e.g. 'BTC'
      quote_str -- e.g. 'USDT'
    """
    if do_verify:
        verify_pair_str(pair_str)

    pair_str = pair_str.replace("/", "-")
    base_str, quote_str = pair_str.split("-")

    if do_verify:
        verify_base_str(base_str)
        verify_quote_str(quote_str)

    return (base_str, quote_str)


# ==========================================================================
# verify..() functions


# @enforce_types
def verify_pairs_str(pairs_str: str):
    """
    @description
      Raise an error if pairs_str is invalid

    @argument
      pairs_str -- e.g. 'ADA/USDT BTC/USDT' or 'ADA-USDT, ETH-RAI'
    """
    pair_str_list = unpack_pairs_str(pairs_str, do_verify=False)
    for pair_str in pair_str_list:
        verify_pair_str(pair_str)


@enforce_types
def verify_pair_str(pair_str: str):
    """
    @description
      Raise an error if pair_str is invalid

    @argument
      pair_str -- e.g. 'ADA/USDT' or 'ETH-RAI'
    """
    pair_str = pair_str.strip()
    if not re.match("[A-Z]+[-/][A-Z]+", pair_str):
        raise ValueError(pair_str)

    base_str, quote_str = unpack_pair_str(pair_str, do_verify=False)
    verify_base_str(base_str)
    verify_quote_str(quote_str)


@enforce_types
def verify_base_str(base_str: str):
    """
    @description
      Raise an error if base_str is invalid

    @argument
      base_str -- e.g. 'ADA' or '   ETH  '
    """
    base_str = base_str.strip()
    if not re.match("[A-Z]+$", base_str):
        raise ValueError(base_str)


@enforce_types
def verify_quote_str(quote_str: str):
    """
    @description
      Raise an error if quote_str is invalid

    @argument
      quote_str -- e.g. 'USDT' or '   RAI  '
    """
    quote_str = quote_str.strip()
    if quote_str not in CAND_USDCOINS:
        raise ValueError(quote_str)
