from typing import List, Union

from enforce_typing import enforce_types


@enforce_types
def safe_fetch_ohlcv(
    exch,
    symbol: str,
    timeframe: str,
    since: int,
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
        print(f"      **WARNING exchange: {e}")
        return None
