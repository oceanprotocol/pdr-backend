from datetime import datetime
import logging
from typing import List, Optional, Union

from enforce_typing import enforce_types
import numpy as np
import requests

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.lake.constants import OHLCV_MULT_MAX, OHLCV_MULT_MIN, BASE_URL_DYDX
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("fetch_ohlcv")


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
      exch -- eg dydx
      symbol -- eg "BTC-USD"
      timeframe -- eg "1HOUR", "5MINS"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max is 100 candles to retrieve,

    @return
      raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}
    """

    try:
        if exch != "dydx":
            return None
        headers = {"Accept": "application/json"}
        response = requests.get(
            f"{BASE_URL_DYDX}/{symbol}?resolution={timeframe}"
            f"&fromISO={since.to_iso_timestr()}&limit={limit}",
            headers=headers,
            timeout=20,
        )
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
                    float_or_none(item["open"]),
                    float_or_none(item["high"]),
                    float_or_none(item["low"]),
                    float_or_none(item["close"]),
                    float_or_none(item["baseTokenVolume"]),
                )
                raw_tohlcv_data.append(ohlcv_tuple)

            return raw_tohlcv_data

        if key_name == "errors" and items:
            errors = items[0]
            error_msg = tuple(errors.items())
            raw_tohlcv_data.append(error_msg)
            return raw_tohlcv_data

        return None

    except Exception as e:
        logger.warning("exchange: %s", e)
        return None


def float_or_none(x: str) -> Optional[float]:
    return float(x) if x is not None else None


@enforce_types
def clean_raw_ohlcv(
    raw_tohlcv_data: Union[list, None],
    feed: ArgFeed,
    st_ut: UnixTimeMs,
    fin_ut: UnixTimeMs,
) -> list:
    """
    @description
      From the raw data coming directly from exchange,
      condition it and account for corner cases.

    @arguments
      raw_tohlcv_data -- output of safe_fetch_ohlcv(), see below
      feed - ArgFeed. eg Binance ETH/USDT
      st_ut -- min allowed time. A timestamp, in ms, in UTC
      fin_ut -- max allowed time. ""

    @return
      tohlcv_data -- cleaned data
    """
    tohlcv_data = raw_tohlcv_data or []
    uts = _ohlcv_to_uts(tohlcv_data)
    uts = _cast_uts_to_int(uts)
    _warn_if_uts_have_gaps(uts, feed.timeframe)

    tohlcv_data = _filter_within_timerange(tohlcv_data, st_ut, fin_ut)

    return tohlcv_data


@enforce_types
def _cast_uts_to_int(uts: list) -> List[int]:
    # this could be done inside _ohlcv_to_uts
    uts = [int(ut) for ut in uts]
    return uts


@enforce_types
def _ohlcv_to_uts(tohlcv_data: list) -> list:
    return [vec[0] for vec in tohlcv_data]


@enforce_types
def _warn_if_uts_have_gaps(uts: List[UnixTimeMs], timeframe: ArgTimeframe):
    if len(uts) <= 1:
        return

    # Ideally, time between ohclv candles is always 5m or 1h
    # But exchange data often has gaps. Warn about worst violations
    diffs_ms = np.array(uts[1:]) - np.array(uts[:-1])  # in ms
    diffs_m = diffs_ms / 1000 / 60  # in minutes
    mn_thr = timeframe.m * OHLCV_MULT_MIN
    mx_thr = timeframe.m * OHLCV_MULT_MAX

    if min(diffs_m) < mn_thr:
        logger.warning("**short candle time: %s min", min(diffs_m))
    if max(diffs_m) > mx_thr:
        logger.warning("long candle time: %s min", max(diffs_m))


@enforce_types
def _filter_within_timerange(
    tohlcv_data: list, st_ut: UnixTimeMs, fin_ut: UnixTimeMs
) -> list:
    uts = _ohlcv_to_uts(tohlcv_data)
    uts = _cast_uts_to_int(uts)
    return [vec for ut, vec in zip(uts, tohlcv_data) if st_ut <= ut <= fin_ut]