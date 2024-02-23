import logging
from typing import List, Union, Tuple

from enforce_typing import enforce_types
import numpy as np

import requests
import polars as pl
import pytz
from datetime import datetime, timedelta

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.timeframe import Timeframe
from pdr_backend.lake.constants import (
    TOHLCV_SCHEMA_PL,
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
def safe_fetch_ohlcv_dydx(
    symbol: str,
    resolution: str,
    st_ut: UnixTimeMs,
    fin_ut: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      calls fetch_dydx_data() but if there's an error it
      emits a warning and returns None, vs crashing everything

    @arguments
      exch -- eg dydx
      symbol -- eg "BTC-USDT"
      timeframe -- eg "1HOUR", "5MINS"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max is 100 candles to retrieve,

    @return
    raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}
    """

    try:
        return fetch_dydx_data(
                    symbol=symbol,
                    resolution=resolution,
                    st_ut=st_ut,
                    fin_ut=fin_ut,
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
def _warn_if_uts_have_gaps(uts: List[UnixTimeMs], timeframe: Timeframe):
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

def fetch_dydx_data(symbol: str, resolution: str, st_ut: UnixTimeMs, fin_ut: UnixTimeMs, limit: int = None) -> Union[List[tuple], None]:
    """
    @description
      makes a loop of get requests for dydx v4 exchange candle data,
        by first converting input params to the correct dydx api syntax ticker: "BTC-USD", resolution: "5MINS", toISO: "2023-10-17T21:00:00.000+00:00",
        then calls the transform_dydx_data() function dydx's,

    @arguments
      exch -- dydx
      symbol -- eg "BTC-USD" or "BTC/USDT"
      timeframe -- eg "5m" or "5MINS"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max # candles to retrieve up to 100

    @return
      df -- a Polars dataframe with schema = TOHLCV_SCHEMA_PL,
      and sorted by timestamp
    """
    # Initialize the empty df
    #all_data = pl.DataFrame([], schema=TOHLCV_SCHEMA_PL)
    all_data = []

    # Int minutes will be used for updating the loop end_time
    resolution_to_minutes = {
        "1MIN": 1,
        "5MINS": 5,
        "15MINS": 15,
        "30MINS": 30,
        "1HOUR": 60,
        "1DAY": 1440,
    }
    minutes = resolution_to_minutes[resolution]

    start_time = UnixTimeMs.to_dt(st_ut)
    end_time = UnixTimeMs.to_dt(fin_ut)

    count = 0

    # Fetch the data in a loop
    while end_time > start_time:
        print(f"Fetching data up to {end_time}")  # Logging

        # Initialize parameters for API request
        end_time = end_time.strftime('%Y-%m-%dT%H:%M:%S')
        params = {'resolution': resolution, 'limit': limit, 'toISO': end_time}

        # Fetch the data
        headers = {'Accept': 'application/json'}
        response = requests.get(
            f'https://indexer.v4testnet.dydx.exchange/v4/candles/perpetualMarkets/{symbol}',
            params=params,
            headers=headers
        )
        data = response.json()

        # Process and add the fetched data to all_data
        if 'candles' in data:

            transformed_data = transform_dydx_data_to_tuples(data['candles'])
            all_data.extend(transformed_data)

            # Update end_time for the next iteration
            end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.UTC)
            end_time = end_time - timedelta(minutes=minutes)

            print("Loop iteration #", count)
            count = count + 1

        else:
            print("No more data returned from dYdX.")
            break  # Exit loop if no data is returned

    all_data = sorted(all_data, key=lambda x: x[0])
    print("all_data tuple list from dydx is ", all_data)

    return all_data

def transform_dydx_data_to_tuples(candles) -> List[Tuple]:
    """
    Transforms dYdX data to a list of tuples
    """
    transformed_data = []

    for candle in candles:
        timestamp_str = candle['startedAt']  # Of the format "2023-01-01T12:00:00.000Z"
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC)

        # Using a helper function to gracefully handle NaNs
        open_price = parse_float(candle['open'])
        high_price = parse_float(candle['high'])
        low_price = parse_float(candle['low'])
        close_price = parse_float(candle['close'])
        volume = parse_float(candle['baseTokenVolume'])

        row = (timestamp,
               open_price,
               high_price,
               low_price,
               close_price,
               volume)

        transformed_data.append(row)

    return transformed_data

def parse_float(value):
    # Attempts to return a float, but if there's an NaN or missing value it
    # catches the error and returns 0.0, vs crashing everything
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0