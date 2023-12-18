from typing import Tuple

import ccxt
from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed
from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv


@enforce_types
def get_trueval(
    feed: Feed, init_timestamp: int, end_timestamp: int
) -> Tuple[bool, bool]:
    """
    @description
        Checks if the price has risen between two given timestamps.
        If the round should be canceled, the second value in the returned tuple is set to True.

    @arguments
        feed -- Feed -- The feed object containing pair details
        init_timestamp -- int -- The starting timestamp.
        end_timestamp -- int -- The ending timestamp.

    @return
        trueval -- did price rise y/n?
        cancel_round -- should we cancel the round y/n?
    """
    symbol = feed.pair
    symbol = symbol.replace("-", "/")
    symbol = symbol.upper()

    # since we will get close price
    # we need to go back 1 candle
    init_timestamp -= feed.seconds_per_epoch
    end_timestamp -= feed.seconds_per_epoch

    # convert seconds to ms
    init_timestamp = int(init_timestamp * 1000)
    end_timestamp = int(end_timestamp * 1000)

    exchange_class = getattr(ccxt, feed.source)
    exchange = exchange_class()
    tohlcvs = safe_fetch_ohlcv(
        exchange, symbol, feed.timeframe, since=init_timestamp, limit=2
    )
    assert len(tohlcvs) == 2, f"expected exactly 2 tochlv tuples. {tohlcvs}"
    init_tohlcv, end_tohlcv = tohlcvs[0], tohlcvs[1]

    if init_tohlcv[0] != init_timestamp:
        raise Exception(
            f"exchange's init_tohlcv[0]={init_tohlcv[0]} should have matched"
            f" target init_timestamp={init_timestamp}"
        )
    if end_tohlcv[0] != end_timestamp:
        raise Exception(
            f"exchange's end_tohlcv[0]={end_tohlcv[0]} should have matched"
            f" target end_timestamp={end_timestamp}"
        )

    init_c, end_c = init_tohlcv[4], end_tohlcv[4]  # c = closing price
    if end_c == init_c:
        trueval = False
        cancel_round = True
        return trueval, cancel_round

    trueval = end_c > init_c
    cancel_round = False
    return trueval, cancel_round
