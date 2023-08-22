"""
Flow
  - reads from subgraph list of template3 contracts, this gets list of all template3 deployed contracts
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
from pdr_backend.trueval.subgraph import Contract


def get_true_val(topic: Contract, initial_timestamp, end_timestamp):
    """Given a topic, Returns the true val between end_timestamp and initial_timestamp
    Topic object looks like:

    {
        "name":"ETH-USDT",
        "address":"0x54b5ebeed85f4178c6cb98dd185067991d058d55",
        "symbol":"ETH-USDT",
        "blocks_per_epoch":"60",
        "blocks_per_subscription":"86400",
        "last_submited_epoch":0,
        "pair":"eth-usdt",
        "base":"eth",
        "quote":"usdt",
        "source":"kraken",
        "timeframe":"5m"
    }

    """
    try:
        exchange_class = getattr(ccxt, topic.source)
        exchange_ccxt = exchange_class()
        price_initial = exchange_ccxt.fetch_ohlcv(
            topic.pair, "1m", since=initial_timestamp, limit=1
        )
        price_end = exchange_ccxt.fetch_ohlcv(
            topic.pair, "1m", since=end_timestamp, limit=1
        )
        return (price_end[0][1] >= price_initial[0][1], price_end[0][1], False)
    except Exception as e:
        return (False, 0, True)
