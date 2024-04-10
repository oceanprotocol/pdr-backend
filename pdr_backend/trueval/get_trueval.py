from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.exchange.fetch_ohlcv import safe_fetch_ohlcv
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
def get_trueval(
    feed: SubgraphFeed,
    init_timestamp_s: UnixTimeS,
    end_timestamp_s: UnixTimeS,
) -> Tuple[bool, bool]:
    """
    @description
        Checks if the price has risen between two given timestamps.
        If the round should be canceled, the second value in the returned tuple is set to True.

    @arguments
        feed -- SubgraphFeed -- The feed object containing pair details
        init_timestamp_s -- int -- The starting timestamp.
        end_timestamp_s -- int -- The ending timestamp.

    @return
        trueval -- did price rise y/n?
        cancel_round -- should we cancel the round y/n?
    """
    symbol = feed.pair
    symbol = symbol.replace("-", "/")
    symbol = symbol.upper()

    # since we will get close price
    # we need to go back 1 candle
    init_timestamp_s = UnixTimeS(init_timestamp_s - feed.seconds_per_epoch)
    end_timestamp_s = UnixTimeS(end_timestamp_s - feed.seconds_per_epoch)

    # convert seconds to ms
    init_timestamp = init_timestamp_s.to_milliseconds()
    end_timestamp = end_timestamp_s.to_milliseconds()

    exchange_str: str = feed.source
    tohlcvs = safe_fetch_ohlcv(
        exchange_str, symbol, feed.timeframe, since=init_timestamp, limit=2
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
        return False, True

    trueval = end_c > init_c
    cancel_round = False
    return trueval, cancel_round
