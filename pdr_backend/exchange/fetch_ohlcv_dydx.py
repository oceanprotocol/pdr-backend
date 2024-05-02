import logging
from datetime import timedelta
from typing import List, Optional, Union

from enforce_typing import enforce_types
import requests

from pdr_backend.cli.arg_pair import verify_pair_str
from pdr_backend.cli.arg_timeframe import verify_timeframe_str
from pdr_backend.exchange.constants import (
    BASE_URL_DYDX,
    TIMEFRAME_TO_DYDX_RESOLUTION,
    TIMEFRAME_TO_DYDX_RESOLUTION_SECONDS,
)
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("fetch_ohlcv_dydx")


@enforce_types
def fetch_ohlcv_dydx(
    pair_str: str,
    timeframe: str,
    since: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      Implementation for dydx:
      Calls dydx's API to get ohlcv data.

      If there's an error,
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
    limit = min(limit, 100) # cannot be greater than 100
    verify_pair_str(pair_str)
    verify_timeframe_str(timeframe)

    baseURL = BASE_URL_DYDX
    ticker = _dydx_ticker(pair_str)
    resolution = _dydx_resolution(timeframe)
    fromISO = since.to_iso_timestr()
    toISO_dt = since.to_dt() + _time_delta_from_timeframe(timeframe, limit)
    toISO = UnixTimeMs(toISO_dt.timestamp() * 1e3).to_iso_timestr()
    headers = {"Accept": "application/json"}
    try:
        s = (
            f"{baseURL}/candles/perpetualMarkets/{ticker}"
            f"?resolution={resolution}&fromISO={fromISO}&toISO={toISO}&limit={limit}"
        )
        response = requests.get(s, headers=headers, timeout=20)

    except Exception as e:
        logger.warning("exchange: %s", e)
        return None

    data = response.json()

    raw_tohlcv_data = []
    key_name = next(iter(data))  # Get the first key in the dict
    items = data[key_name]

    if key_name == "candles" and items:
        for item in items:
            t_iso_str = item["startedAt"]
            t_UnixTimeMs = UnixTimeMs.from_iso_timestr(t_iso_str)
            assert t_iso_str == t_UnixTimeMs.to_iso_timestr()
            tohlcv_tup = (
                t_UnixTimeMs,
                _float_or_none(item["open"]),
                _float_or_none(item["high"]),
                _float_or_none(item["low"]),
                _float_or_none(item["close"]),
                _float_or_none(item["baseTokenVolume"]),
            )
            raw_tohlcv_data.append(tohlcv_tup)
        # reverse for compatibility with ccxt
        return list(reversed(raw_tohlcv_data))

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
    Eg given 'BTC/USDT', returns 'BTC-USD'
    """
    verify_pair_str(pair_str)
    return pair_str.replace("/", "-").replace("USDT", "USD")


@enforce_types
def _dydx_resolution(timeframe: str):
    """
    Compute a timeframe friendly for dydx.
    Eg given '5m', returns '5MINS'
    """
    verify_timeframe_str(timeframe)
    if timeframe not in TIMEFRAME_TO_DYDX_RESOLUTION:
        raise ValueError(f"Don't currently support timeframe={timeframe}")
    return TIMEFRAME_TO_DYDX_RESOLUTION[timeframe]


@enforce_types
def _float_or_none(x: Optional[str]) -> Optional[float]:
    return None if x is None else float(x)


def _time_delta_from_timeframe(timeframe: str, limit: int) -> timedelta:
    # Convert timeframe and limit to a timedelta.
    if timeframe not in TIMEFRAME_TO_DYDX_RESOLUTION_SECONDS:
        raise ValueError(f"Don't currently support timeframe={timeframe}")
    second_duration = TIMEFRAME_TO_DYDX_RESOLUTION_SECONDS[timeframe]
    return timedelta(seconds=second_duration * limit)
