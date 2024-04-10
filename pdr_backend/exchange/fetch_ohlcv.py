from datetime import datetime
import logging
from typing import List, Optional, Union

from enforce_typing import enforce_types
import requests

from pdr_backend.cli.arg_exchange import verify_exchange_str
from pdr_backend.cli.arg_pair import verify_pair_str
from pdr_backend.cli.arg_timeframe import verify_timeframe_str
from pdr_backend.exchange.constants import (
    BASE_URL_DYDX,
    TIMEFRAME_TO_DYDX_RESOLUTION,
)
from pdr_backend.exchange.exchange_mgr import ExchangeMgr
from pdr_backend.ppss.exchange_mgr_ss import ExchangeMgrSS
from pdr_backend.util.constants import CAND_TIMEFRAMES
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("fetch_ohlcv")


@enforce_types
def safe_fetch_ohlcv(
    exchange_str: str,
    pair_str: str,
    timeframe: str,
    since: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
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
        return safe_fetch_ohlcv_dydx(pair_str, timeframe, since, limit)
    return safe_fetch_ohlcv_ccxt(exchange_str, pair_str, timeframe, since, limit)


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
      calls ccxt.exchange.fetch_ohlcv() but if there's an error it
      emits a warning and returns None, vs crashing everything

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

    # Soon, we'll move fetch_ohlcv* into a proper Exchange class,
    # which will have a proper ss. And then the following lines will
    # be deprecated or replaced
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


@enforce_types
def safe_fetch_ohlcv_dydx(
    pair_str: str,
    timeframe: str,
    since: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      Calls dydx's API to get ohlcv data. If there's an error,
      it emits a warning and returns None, vs crashing everything.

    @arguments
      pair_str -- eg "BTC/USDT". NOT "BTC-USDT"
      timeframe -- eg "1h", "5m". NOT eg "5MINS"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max is 100 candles to retrieve,

    @return
      raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}

    @notes
      Dydx candles API docs:
      https://docs.dydx.exchange/developers/indexer/indexer_api#getcandles
    """
    verify_pair_str(pair_str)
    if "-" in pair_str:
        raise ValueError(f"Got pair_str={pair_str}. It must have '/' not '-'")
    verify_timeframe_str(timeframe)

    ticker = _dydx_ticker(pair_str)
    resolution = _dydx_resolution(timeframe)
    fromISO = since.to_iso_timestr()
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(
            f"{BASE_URL_DYDX}/candles/perpetualMarkets/{ticker}"
            f"?resolution={resolution}&fromISO={fromISO}&limit={limit}",
            headers=headers,
            timeout=20,
        )

    except Exception as e:
        logger.warning("exchange: %s", e)
        return None

    data = response.json()

    raw_tohlcv_data = []
    key_name = next(iter(data))  # Get the first key in the dict
    items = data[key_name]

    if key_name == "candles" and items:
        for item in items:
            dt = datetime.strptime(item["startedAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp = int(dt.timestamp() * 1000)
            ohlcv_tuple = (
                timestamp,
                _float_or_none(item["open"]),
                _float_or_none(item["high"]),
                _float_or_none(item["low"]),
                _float_or_none(item["close"]),
                _float_or_none(item["baseTokenVolume"]),
            )
            raw_tohlcv_data.append(ohlcv_tuple)

        return raw_tohlcv_data

    if key_name == "errors" and items:
        errors = items[0]
        error_msg = tuple(errors.items())
        raw_tohlcv_data.append(error_msg)
        return raw_tohlcv_data

    return None


@enforce_types
def _dydx_ticker(pair_str: str):
    """
    Compute a pair_str friendly for dydx.
    Eg given 'BTC/USDT', returns 'BTC-USDT'
    """
    verify_pair_str(pair_str)
    if "-" in pair_str:
        raise ValueError(f"Got pair_str={pair_str}. It must have '/' not '-'")
    return pair_str.replace("/", "-")


@enforce_types
def _dydx_resolution(timeframe: str):
    """
    Compute a timeframe friendly for dydx.
    Eg given '5m', returns '5MINS'
    """
    if timeframe not in CAND_TIMEFRAMES:
        raise ValueError(f"Got timeframe={timeframe}. Should be 1m, 5m, ...")
    if timeframe not in TIMEFRAME_TO_DYDX_RESOLUTION:
        raise ValueError(f"Don't currently support timeframe={timeframe}")
    return TIMEFRAME_TO_DYDX_RESOLUTION[timeframe]


@enforce_types
def _float_or_none(x: Optional[str]) -> Optional[float]:
    return None if x is None else float(x)
