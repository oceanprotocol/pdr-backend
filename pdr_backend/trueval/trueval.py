"""
Flow
  - reads from subgraph list of dt3 contracts, to get all deployed contracts
  - for every contract, monitors when epoch is changing
  - once an epoch is ended, calculate the true_val and submit.

Notes on customization:

  The actual true_val is fetched by calling function get_true_val()

  We call get_true_val() with 4 args:
   - topic: this is pair object
   - initial_timestamp:   blocktime for begining of epoch - 2
   - end_timestamp:   blocktime for begining of epoch -1

  Then it returns true_val, which gets submitted to contract

  You need to change the code to support more complex flows. Now, it's based on ccxt
"""

import ccxt
from pdr_backend.models.contract_data import ContractData


def get_true_val(topic: ContractData, initial_timestamp, end_timestamp):
    """Given a topic, Returns the true val between end_timestamp and initial_timestamp
    Topic object looks like:

    {
        "name":"ETH-USDT",
        "address":"0x54b5ebeed85f4178c6cb98dd185067991d058d55",
        "symbol":"ETH-USDT",
        "blocks_per_epoch":"60",
        "blocks_per_subscription":"86400",
        "pair":"eth-usdt",
        "base":"eth",
        "quote":"usdt",
        "source":"kraken",
        "timeframe":"5m"
    }

    """
    symbol = topic.pair
    if topic.source == "binance" or topic.source == "kraken":
        symbol = symbol.replace("-", "/")
        symbol = symbol.upper()
    try:
        exchange_class = getattr(ccxt, topic.source)
        exchange_ccxt = exchange_class()
        price_initial = exchange_ccxt.fetch_ohlcv(
            symbol, "1m", since=initial_timestamp, limit=1
        )
        price_end = exchange_ccxt.fetch_ohlcv(
            symbol, "1m", since=end_timestamp, limit=1
        )
        return (price_end[0][1] >= price_initial[0][1], False)
    except Exception as e:
        print(f"Error getting trueval for {symbol} {e}")
        return (False, True)
