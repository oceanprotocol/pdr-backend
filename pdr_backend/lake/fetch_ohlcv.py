from datetime import datetime
import logging
from typing import List, Optional, Union

from enforce_typing import enforce_types
import requests

from pdr_backend.lake.constants import (
    BASE_URL_DYDX,
    TIMEFRAME_TO_DYDX_RESOLUTION,
)
from pdr_backend.util.constants import CAND_TIMEFRAMES
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("fetch_ohlcv")


@enforce_types
def safe_fetch_ohlcv(
    exch,
    symbol: str,
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
      exch -- eg "dydx", ccxt.binanceus(), or ccxt.kraken()
      symbol -- eg "BTC/USDT". NOT "BTC-USDT"
      timeframe -- eg "1h", "1m"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max # candles to retrieve

    @return
      raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}
    """
    if isinstance(exch, str):
        if exch == "dydx":
            return safe_fetch_ohlcv_dydx(symbol, timeframe, since, limit)
        raise ValueError(exch)
    return safe_fetch_ohlcv_ccxt(exch, symbol, timeframe, since, limit)


@enforce_types
def safe_fetch_ohlcv_ccxt(
    exch,
    symbol: str,
    timeframe: str,
    since: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      calls ccxt.exchange.fetch_ohlcv() but if there's an error it
      emits a warning and returns None, vs crashing everything

    @arguments
      exch -- eg ccxt.binanceus()
      symbol -- eg "BTC/USDT". NOT "BTC-USDT"
      timeframe -- eg "1h", "1m"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max # candles to retrieve

    @return
      raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}
    """
    if "-" in symbol:
        raise ValueError(f"Got symbol={symbol}. It must have '/' not '-'")
    if timeframe not in CAND_TIMEFRAMES:
        raise ValueError(f"Got timeframe={timeframe}. Should be 1m, 5m, ...")

    try:
        return exch.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
        )
    except Exception as e:
        logger.warning("exchange: %s", e)
        return None


@enforce_types
def safe_fetch_ohlcv_dydx(
    symbol: str,
    timeframe: str,
    since: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      Calls dydx's API to get ohlcv data. If there's an error,
      it emits a warning and returns None, vs crashing everything.

    @arguments
      symbol -- eg "BTC/USDT". NOT "BTC-USDT"
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
    ticker = _dydx_ticker(symbol)
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
def _dydx_ticker(symbol: str):
    """
    Compute a symbol friendly for dydx.
    Eg given 'BTC/USDT', returns 'BTC-USDT'
    """
    if "-" in symbol:
        raise ValueError(f"Got symbol={symbol}. It must have '/' not '-'")
    return symbol.replace("/", "-")


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
