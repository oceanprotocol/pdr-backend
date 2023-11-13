from typing import List, Tuple

from enforce_typing import enforce_types

from pdr_backend.util.constants import CAND_SIGNALS


@enforce_types
def unpack_pair_str(pair_str: str) -> Tuple[str, str]:
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
    pairstr = pair_str.replace("/", "-")
    base_str, quote_str = pairstr.split("-")
    return (base_str, quote_str)


@enforce_types
def unpack_pairs_str(pairs_str: str) -> List[str]:
    """
    @description
      Unpack the string for *one or more* pairs, into list of pair_str

      Example: Given 'ADA/USDT, BTC/USDT, ETH/USDT'
      Return ['ADA/USDT', 'BTC/USDT', 'ETH/USDT']

    @argument
      pairs_str - '<base>/<quote>' or 'base-quote'

    @return
      pairs_list -- List[<pair_str>]
    """
    pairs_str = pairs_str.replace(", ", ",").replace(" ", ",")
    pairs_list = pairs_str.split(",")
    return pairs_list


@enforce_types
def unpack_feed_str(feed_str: str) -> Tuple[str, str, str]:
    """
    @description
      Unpack the string for a *single* feed: 1 exchange, 1 signal, 1 pair
      Given e.g. 'binance oc ADA/USDT BTC/USDT'
      Return ('binance', 'open', 'BTC/USDT')

    @return
      exchange_id -- str - e.g. 'binance'
      signal -- str - e.g. 'open'
      pair_str -- str - e.g. 'BTC/USDT'
    """
    feeds_str = feed_str
    (exchange_id, signals, pairs_str) = unpack_feeds_str(feeds_str)
    assert len(signals) == 1 and len(pairs_str) == 1
    signal, pair_str = signals[0], pairs_str[0]
    return (exchange_id, signal, pair_str)


@enforce_types
def unpack_feeds_str(feeds_str: str) -> Tuple[str, List[str], List[str]]:
    """
    @description
      Example: Given 'binance oc ADA/USDT BTC/USDT'
      Return  ('binance', ['open', close'], ['ADA/USDT', 'BTC/USDT'])

    @arguments
      feeds_str - '<exchange_id> <signal chars subset of 'ohclv'> <pairs_str>

    @return
      exchange_id -- str - e.g. 'binance'
      signals -- List[str] - e.g. ['open', 'close']
      pairs -- List[str] - e.g. ['ADA/USDT', 'BTC/USDT']
    """
    exchange_id, chars_str, pairs_str = feeds_str.split(" ", maxsplit=2)
    signals = [
        cand_signal  # e.g. "c"
        for cand_signal in CAND_SIGNALS  # ["open", "high", ..]
        if cand_signal[0] in chars_str
    ]
    pairs = unpack_pairs_str(pairs_str)
    return (exchange_id, signals, pairs)
