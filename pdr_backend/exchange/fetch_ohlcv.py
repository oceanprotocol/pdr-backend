import logging
from typing import List, Union

from enforce_typing import enforce_types

from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.exchange.fetch_ohlcv_ccxt import fetch_ohlcv_ccxt
from pdr_backend.exchange.fetch_ohlcv_dydx import fetch_ohlcv_dydx

logger = logging.getLogger("fetch_ohlcv")


@enforce_types
def fetch_ohlcv(
    exchange_str: str,
    pair_str: str,
    timeframe: str,
    since: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      Top-level switch:
      Get ohlcv data from dydx exchange, or an exchange supported by ccxt.

      If there's an error it emits a warning and returns None,
      vs crashing everything

    @arguments
      exchange_str -- eg "dydx", "binance", "kraken"
      pair_str -- eg "BTC/USDT". NOT "BTC-USDT"
      timeframe -- eg "1h", "1m"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max # candles to retrieve

    @return
      raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}
    """
    if exchange_str == "dydx":
        return fetch_ohlcv_dydx(pair_str, timeframe, since, limit)
    return fetch_ohlcv_ccxt(exchange_str, pair_str, timeframe, since, limit)
