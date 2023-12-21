import re
from typing import List, Optional, Tuple, Union

from enforce_typing import enforce_types

from pdr_backend.util.constants import CAND_USDCOINS

# convention: it allows "-" and "/" as input, and always outputs "/".

# note: the only place that "/" doesn't work is filenames.
#   So it converts to "-" just-in-time. That's outside this module.


class ArgPair:
    def __init__(self, pair_str: Optional[str] = None, base_str: Optional[str] = None, quote_str: Optional[str] = None):
        if not pair_str and [None in [base_str, quote_str]]:
            raise ValueError("Must provide either pair_str, or both base_str and quote_str")

        if isinstance(pair_str, ArgPair):
            pair_str = str(pair_str)

        if pair_str is None:
            pair_str = f"{base_str}/{quote_str}"
        else:
            pair_str = pair_str.strip()
            if not re.match("[A-Z]+[-/][A-Z]+", pair_str):
                raise ValueError(pair_str)

            base_str, quote_str = _unpack_pair_str(pair_str)

        _verify_base_str(base_str)
        _verify_quote_str(quote_str)

        self.pair_str = pair_str
        self.base_str = base_str
        self.quote_str = quote_str

    def __eq__(self, other):
        return self.pair_str == str(other)

    def __str__(self):
        return f"{self.base_str}/{self.quote_str}"

    def __hash__(self):
        return hash(self.pair_str)


class ArgPairs(List[ArgPair]):
    @staticmethod
    def from_str(pairs_str: str) -> 'ArgPairs':
        pairs = ArgPairs([pair for pair in _unpack_pairs_str(pairs_str)])

        if not pairs:
            raise ValueError(pairs_str)

        return pairs

    def __eq__(self, other):
        return set(self) == set(other)

    def __init__(self, pairs: Union[List[str], List[ArgPair]]):
        if not isinstance(pairs, list):
            raise TypeError(pairs)

        if not pairs:
            raise ValueError(pairs)

        pairs = [ArgPair(pair) for pair in pairs if pair]
        super().__init__(pairs)

    @enforce_types
    def __str__(self) -> Union[ArgPair, None]:
        """
        Example: Given ArgPairs ["BTC/USDT","ETH-DAI"]
        Return "BTC/USDT,ETH/DAI"
        """
        return ",".join([str(pair) for pair in self])


@enforce_types
def _unpack_pairs_str(pairs_str: str) -> List[str]:
    """
    @description
      Unpack the string for *one or more* pairs, into list of pair_str

      Example: Given 'ADA-USDT, BTC/USDT, ETH/USDT'
      Return ['ADA/USDT', 'BTC/USDT', 'ETH/USDT']

    @argument
      pairs_str - '<base>/<quote>' or 'base-quote'

    @return
      pair_str_list -- List[<pair_str>], where all "-" are "/"
    """
    pairs_str = pairs_str.strip()
    pairs_str = " ".join(pairs_str.split())  # replace multiple whitespace w/ 1
    pairs_str = pairs_str.replace(", ", ",").replace(" ,", ",")
    pairs_str = pairs_str.replace(" ", ",")
    pairs_str = pairs_str.replace("-", "/")  # ETH/USDT -> ETH-USDT. Safer files.
    pair_str_list = pairs_str.split(",")

    if not pair_str_list:
        raise ValueError(pairs_str)

    return pair_str_list


def _unpack_pair_str(pair_str: str) -> Tuple[str, str]:
    """
    @description
      Unpack the string for a *single* pair, into base_str and quote_str.

      Example: Given 'BTC/USDT' or 'BTC-USDT'
      Return ('BTC', 'USDT')

    @argument
      pair_str - '<base>/<quote>' or 'base-quote'

    @return
      base_str -- e.g. 'BTC'
      quote_str -- e.g. 'USDT'
    """
    pair_str = pair_str.replace("/", "-")
    base_str, quote_str = pair_str.split("-")

    return (base_str, quote_str)


@enforce_types
def _verify_base_str(base_str: str):
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
def _verify_quote_str(quote_str: str):
    """
    @description
      Raise an error if quote_str is invalid

    @argument
      quote_str -- e.g. 'USDT' or '   RAI  '
    """
    quote_str = quote_str.strip()
    if quote_str not in CAND_USDCOINS:
        raise ValueError(quote_str)
