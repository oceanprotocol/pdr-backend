import logging
from typing import List, Union

from enforce_typing import enforce_types
import requests

from pdr_backend.cli.arg_exchange import verify_exchange_str
from pdr_backend.cli.arg_pair import verify_pair_str
from pdr_backend.cli.arg_timeframe import verify_timeframe_str
from pdr_backend.exchange.exchange_mgr import ExchangeMgr
from pdr_backend.ppss.exchange_mgr_ss import ExchangeMgrSS
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("fetch_ohlcv_ccxt")

@enforce_types
def safe_fetch_ohlcv_ccxt(
    exchange_str: str,
    pair_str: str,
    timeframe: str,
    since: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      Implementation for ccxt:
      calls ccxt.exchange.fetch_ohlcv()

      If there's an error it emits a warning and returns None,
      vs crashing everything

    @arguments
      exchange_str -- eg "binance", "kraken"
      pair_str -- eg "BTC/USDT". NOT "BTC-USDT"
      timeframe -- eg "1h", "1m"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max # candles to retrieve

    @return
      raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}
    """
    verify_exchange_str(exchange_str)
    if exchange_str == "dydx":
        raise ValueError(exchange_str)
    verify_pair_str(pair_str)
    if "-" in pair_str:
        raise ValueError(f"Got pair_str={pair_str}. It must have '/' not '-'")
    verify_timeframe_str(timeframe)

    d = {"timeout": 30, "ccxt_params": {}, "dydx_params": {}}
    ss = ExchangeMgrSS(d)
    exchange_mgr = ExchangeMgr(ss)
    exchange = exchange_mgr.exchange(exchange_str)

    try:
        return exchange.fetch_ohlcv(
            symbol=pair_str,
            timeframe=timeframe,
            since=since,
            limit=limit,
        )
    except Exception as e:
        logger.warning("exchange: %s", e)
        return None

