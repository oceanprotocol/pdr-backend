"""
Flow
- reads from subgraph list of template3 contracts, this gets list of all template3 deployed contracts
- for every contract, monitors when epoch is changing
- once we can predict a value, we call predict_function in predict.py. See below

Notes on customization:

  The actual prediction code is in *this file*, in predict_function().

  We call predict_function() with 2 args:
   - topic:  this is pair object
   - estimated_time:  estimated timestamp of block that we are going to predict.   This is informal, blockchain mining time is not accurate

  It returns two variables:
   - predicted_value:  boolean, up/down
   - predicted_confidence:   int, 1 -> 100%. This sets the stake (STAKE_AMOUNT * predicted_confidence/100) that you are willing to put in your prediction.

  You need to change the function code and do some of your stuff. Now, it's just doing some random predictions

## About BLOCKS_TILL_EPOCH_END

(Note: this may become obsolete with the new definition of epoch based on 'epoch_start'. If that's the case, delete this section:)

  If we want to predict the value for epoch E, we need to do it in epoch E - 2 (latest.  Of course, we could predict values for a distant epoch in the future if we want to)
  And to do so, our tx needs to be confirmed in the last block of epoch (otherwise, it's going to be part of next epoch and our prediction tx will revert)

  But, for every prediction, there are some steps involved, each one taking it's toll on duration:
    - the actual prediction code
    - time to generate the tx
    - time until your pending tx in mempool is picked by miner
    - time until your tx is confirmed in a block

  You can control how early to predict, taking the above in consideration, using env BLOCKS_TILL_EPOCH_END.
  It's translation is:  With how many blocks in advanced untill epoch end do we start the prediction process.
  The default value is 5, which leaves us enough time.  (Ie: if block generation duration is 12 sec, we have 60 seconds to do our job)


## TO DO
  - [ ]  - improve payouts collect flow
  - [ ]  - check for balances
  - [ ]  - improve approve/allowence flow
"""

import ccxt
import random


def predict_function(topic, estimated_time):
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
        f" We were asked to predict {topic['name']} (contract: {topic['address']}) value at estimated timestamp: {estimated_time}"
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
