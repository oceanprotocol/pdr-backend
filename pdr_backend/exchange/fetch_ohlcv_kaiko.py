import logging
import os

from typing import List, Union
import requests

from enforce_typing import enforce_types

from pdr_backend.util.time_types import UnixTimeMs


logger = logging.getLogger("fetch_ohlcv_kaiko")


def exchange_str_to_kaiko(exchange_str: str):
    if exchange_str == "binance":
        return "binc"
    return exchange_str


def convert_to_tohlcv(data):
    # Create a list to hold the TOHLCV tuples
    raw_tohlcv_data = []

    # Iterate through each dictionary in the all_data list
    for entry in data:
        # Extract and convert the relevant fields
        if entry["close"] is None:
            continue
        timestamp = int(entry["timestamp"])
        open_ = float(entry["open"])
        high = float(entry["high"])
        low = float(entry["low"])
        close = float(entry["close"])
        volume = float(entry["volume"])

        # Create a tuple with the required format and append to the list
        tohlcv_tuple = (timestamp, open_, high, low, close, volume)
        raw_tohlcv_data.append(tohlcv_tuple)

    # Sort the list of tuples by timestamp (ascending order)
    raw_tohlcv_data.sort(key=lambda x: x[0])

    return raw_tohlcv_data


@enforce_types
def fetch_ohlcv_kaiko(
    exchange_str: str,
    pair_str: str,
    timeframe: str,
    since: UnixTimeMs,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      Implementation for kaiko:

      If there's an error it emits a warning and returns None,
      vs crashing everything

    @arguments
      exchange_str -- eg "binc"
      pair_str -- eg "btc-usdt". NOT "BTC/USDT"
      timeframe -- eg "1h", "1m", "1s"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max # candles to retrieve

    @return
      raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}
    """
    exchange_str = exchange_str_to_kaiko(exchange_str)
    pair_str = pair_str.replace("\\", "-").lower()
    base = "https://us.market-api.kaiko.io/v2/data/trades.v1/exchanges/"
    path = f"{exchange_str}/spot/{pair_str}/aggregations/ohlcv?interval={timeframe}"
    url = f"{base}{path}"
    api_key = os.getenv("KAIKO_KEY")
    if not api_key:
        raise ValueError("No KAIKO_KEY env var found")
    headers = {"X-Api-Key": api_key}
    all_data = []
    continue_token = None
    page_size = 100000  # max page size
    start_time = since.to_dt().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"

    while len(all_data) < limit:
        params = {"page_size": page_size}
        if len(all_data) == 0:
            if start_time:
                params["start_time"] = start_time
        if continue_token:
            params["continuation_token"] = continue_token

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data["data"])
            continue_token = data.get("continuation_token", None)
            if not continue_token:
                break  # No more pages to fetch
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break

    return convert_to_tohlcv(all_data)
