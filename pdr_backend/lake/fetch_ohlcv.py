import logging
from typing import List, Union

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.lake.constants import (
    OHLCV_MULT_MAX,
    OHLCV_MULT_MIN,
)
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
    _warn_if_uts_have_gaps(uts, feed.timeframe)

    tohlcv_data = _filter_within_timerange(tohlcv_data, st_ut, fin_ut)

    return tohlcv_data


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
    return [vec for ut, vec in zip(uts, tohlcv_data) if st_ut <= ut <= fin_ut]
