import logging
from typing import List, Union

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.lake.constants import OHLCV_MULT_MAX, OHLCV_MULT_MIN
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("clean_raw_ohlcv")


@enforce_types
def clean_raw_ohlcv(
    raw_tohlcv_data: Union[list, None],
    feed: ArgFeed,
    st_ut: UnixTimeMs,
    fin_ut: UnixTimeMs,
) -> list:
    """
    @description
      From the raw data coming directly from exchange via fetch_ohlcv(),
      condition it and account for corner cases.

    @arguments
      raw_tohlcv_data -- output of fetch_ohlcv(), see below
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
