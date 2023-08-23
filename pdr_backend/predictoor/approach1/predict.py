"""
Flow
 - Fetches a list of Predictoor contracts from subgraph and filters them based on the filters set.
 - Monitors each contract for epoch changes.
 - When a value can be predicted, the `predict_function` in predict.py is called.
Notes on customization:

## Predict Function
  The actual prediction code is in *this file*, in predict_function().

  The function is called with 2 arguments:

  - topic: Information about the trading pair.
  - timestamp: Timestamp of the prediction.

  The function should return:

  - predicted_value: Boolean, indicating the prediction direction (True for up, False for down).
  - predicted_confidence: Integer between 1 and 100. Represents the confidence level in the prediction.
  - stake_amount: Amount of tokens to stake for the prediction.

  By default, `predict_function` uses random values for predictions. You need to customize it and implement your own strategy.

## Topic Object

  The topic object has all the details about the pair:

  - `name` - The name of the trading pair, e.g., "ETH-USDT".
  - `symbol` - Symbol of the trading pair.
  - `base` - Base currency of the trading pair.
  - `quote` - Quote currency of the trading pair.
  - `source` - Source exchange or platform.
  - `timeframe` - Timeframe for the trade signal, e.g., "5m" for 5 minutes.

## About SECONDS_TILL_EPOCH_END

  If we want to predict the value for epoch E, we need to do it in epoch E - 2 (latest.  Of course, we could predict values for a distant epoch in the future if we want to)
  And to do so, our tx needs to be confirmed in the last block of epoch (otherwise, it's going to be part of next epoch and our prediction tx will revert)

  But, for every prediction, there are some steps involved, each one taking it's toll on duration:
    - the actual prediction code
    - time to generate the tx
    - time until your pending tx in mempool is picked by miner
    - time until your tx is confirmed in a block

  Adjust the environment variable `SECONDS_TILL_EPOCH_END` to control how many seconds in advance of the epoch ending you want the prediction process to start. A predictoor can submit multiple predictions, however, only the final submission made before the deadline is considered valid.

  To clarify further: if this value is set to 60, the predictoor will be asked to predict in every block during the last 60 seconds before the epoch concludes.

## TO DO
  - [ ]  - improve payouts collect flow
  - [ ]  - check for balances
  - [ ]  - improve approve/allowence flow
"""

import ccxt
import random


def predict_function(topic, timestamp):
    """Given a topic, let's predict
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
    print(
        f" We were asked to predict {topic['name']} (contract: {topic['address']}) value at estimated timestamp: {timestamp}"
    )
    predicted_confidence = None
    predicted_value = None

    try:
        predicted_value = bool(random.getrandbits(1))
        predicted_confidence = random.randint(1, 100)

        """ Or do something fancy, like:
        
        exchange_class = getattr(ccxt, topic["source"])
        exchange_ccxt = exchange_class()
        candles = exchange_ccxt.fetch_ohlcv(topic['pair'], topic['timeframe'])
        #if price is not moving, let's not predict anything
        if candles[0][1] != candles[1][1]:
            #just follow the trend.  True (up) is last close price > previous close price, False (down) otherwise
            predicted_confidence = random.randint(1,100)
            predicted_value = True if candles[0][1]>candles[1][1] else False
            print(f"Predicting {predicted_value} with a confidence of {predicted_confidence}")
        
        """
    except Exception as e:
        print(e)
        pass
    return (predicted_value, predicted_confidence)
