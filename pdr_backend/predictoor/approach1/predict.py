def get_prediction(feed: dict, timestamp: str):
    """
    @description
      Given a feed, let's predict for a given timestamp.

    @arguments
      feed -- dict -- info about the trading pair. See appendix
      timestamp -- str -- when to make prediction for

    @return
      predval -- bool -- if True, it's predicting 'up'. If False, 'down'
      stake -- float -- amount to stake, in units of ETH (vs wei)

    @notes
      Below is the defualt implementation, giving random predictions.
      You need to customize it to implement your own strategy.

    @appendix 
      The feed dict looks like:
      {
        "name" : "ETH-USDT", # name of trading pair
        "address" : "0x54b5ebeed85f4178c6cb98dd185067991d058d55", # DT3 contract
    
        "symbol" : "ETH-USDT", # symbol of the trading pair
        "pair" : "eth-usdt", # (??, see line above)
        "base" : "eth", # base currency of trading pair
        "quote" : "usdt", # quote currency of the trading pair (??, see line above)
        "source" : "kraken", # source exchange or platform
        "timeframe" : "5m", # timeframe for the trade signal. 5m = 5 minutes

        # you could pass in other info
        "previous_submitted_epoch" : 0,
        "blocks_per_epoch" : "60", 
        "blocks_per_subscription" : "86400",
      }

    ## About SECONDS_TILL_EPOCH_END

    If we want to predict the value for epoch E, we need to do it in epoch E - 2
    (latest.  Though we could predict for a distant future epoch if desired)
   
    And to do so, our tx needs to be confirmed in the last block of epoch
    (otherwise, it's going to be part of next epoch and our prediction tx
     will revert)

    But, for every prediction, there are several steps. Each takes time:
    - time to compute prediction (e.g. run model inference)
    - time to generate the tx
    - time until your pending tx in mempool is picked by miner
    - time until your tx is confirmed in a block

    To help, you can set envvar `SECONDS_TILL_EPOCH_END`. It controls how many
    seconds in advance of the epoch ending you want the prediction process to
    start. A predictoor can submit multiple predictions. However, only the final
    submission made before the deadline is considered valid.

    To clarify further: if this value is set to 60, the predictoor will be asked
    to predict in every block during the last 60 seconds before the epoch
    concludes.
    """
    print(
        f" We were asked to predict {feed['name']} "
        f"(contract: {feed['address']}) value "
        f"at estimated timestamp: {timestamp}"
    )

    # Pick random prediction & random stake. You need to customize this.
    import random
    predval = bool(random.getrandbits(1))
    stake = random.randint(1, 100)

    return (predval, stake)


# ## An example of something a bit fancier. See approach2 for fancier yet.

# exchange_class = getattr(ccxt, feed["source"])
# exchange_ccxt = exchange_class()
# candles = exchange_ccxt.fetch_ohlcv(feed['pair'], feed['timeframe'])
# #if price is not moving, let's not predict anything
# if candles[0][1] != candles[1][1]:
#     #just follow the trend:
#     #   True (up) is last close price > previous close price,
#     #   False (down) otherwise
#     stake = random.randint(1,100)
#     predval = True if candles[0][1]>candles[1][1] else False
#     print(f"Predicting {predval} with a confidence of {predicted_confidence}")
