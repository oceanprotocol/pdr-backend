import logging
import os

from typing import List, Union
import requests

from enforce_typing import enforce_types

from pdr_backend.util.time_types import UnixTimeMs


logger = logging.getLogger("fetch_ohlcv_kaiko")


@enforce_types
def exchange_str_to_kaiko(exchange_str: str):
    if exchange_str == "binance":
        return "binc"
    return exchange_str

@enforce_types
def convert_to_tohlcv(data):
    def extract_fields(entry):
        return (
            int(entry["timestamp"]),
            float(entry["open"]),
            float(entry["high"]),
            float(entry["low"]),
            float(entry["close"]),
            float(entry["volume"])
        )
    
    raw_tohlcv_data = []
    last_valid_entry = None

    for entry in data:
        if entry["close"] is None:
            if last_valid_entry is None:
                # Find the next valid entry with a non-None 'close'
                for future_entry in data[data.index(entry) + 1:]:
                    if future_entry["close"] is not None:
                        last_valid_entry = extract_fields(future_entry)
                        break
            
            if last_valid_entry:
                raw_tohlcv_data.append((
                    int(entry["timestamp"]),
                    *last_valid_entry[1:]
                ))
        else:
            tohlcv_tuple = extract_fields(entry)
            last_valid_entry = tohlcv_tuple
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
    pair_str = pair_str.replace("\\", "-").replace("/", "-").lower()
    base = "https://us.market-api.kaiko.io/v2/data/trades.v1/exchanges/"
    path = f"{exchange_str}/spot/{pair_str}/aggregations/ohlcv?interval={timeframe}"
    url = f"{base}{path}"
    api_key = os.getenv("KAIKO_KEY")
    if not api_key:
        raise ValueError("No KAIKO_KEY env var found")
    headers = {"X-Api-Key": api_key}
    all_data: List[dict] = []
    page_size = limit  # max page size
    start_time = since.to_dt().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"
    params = {"page_size": page_size, "start_time": start_time, "sort": "asc"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["result"] == "error":
            raise ValueError(f"Error: {data['message']}")
        all_data.extend(data["data"])

    return convert_to_tohlcv(all_data)
