# Trader

The main action happens in the trade function of `trade.py`. This function kicks in when there's a signal for a specific trading pair, like ETH-USDT. The topic object gives all the details about the pair. The direction parameter is a tuple: the first element shows the stake_up amount, and the second shows the total staked.

## Trade function

`trade.py` contains the `trade` function which is a placeholder for your trading strategy. This function is called whenever there's a new signal. When called, it receives two parameters:

- topic: A dictionary containing details about the trading pair.
- direction: A tuple where the first element represents `stake_up` and the second denotes `total_stake`. Actions can be taken based on the proportion staked on each side and the overall staked amounts.

By default, `trade` function only prints the incoming trading signal. You need to modify it and implement your trading strategy.

### Topic Object

The topic object is structured as follows:

- `name` - The name of the trading pair, e.g., "ETH-USDT".
- `address` - Contract address of the datatoken.
- `symbol` - Symbol of the trading pair.
- `seconds_per_epoch` - Number of seconds per epoch.
- `seconds_per_subscription` - Number of seconds per subscription.
- `last_submited_epoch` - Last submitted epoch count.
- `pair` - Another representation of the trading pair.
- `base` - Base currency of the trading pair.
- `quote` - Quote currency of the trading pair.
- `source` - Source exchange or platform.
- `timeframe` - Timeframe for the trade signal, e.g., "5m" for 5 minutes.

## Instructions

- [Install pdr-backend](../../../READMEs/install.md)
- Customization
        - Go to trade.py. Here, you'll find the [trade](#trade-function) function. Modify the trade function to implement your trading strategy.
- [Run trader agent](../../../READMEs/running-an-agent.md)

## Notes

- The direction parameter provides two key numbers: the first represents the amount staked by predictors betting on price going up (stake_up), while the second captures the total amount staked by all predictors. As a trader, you can leverage these numbers to make informed decisions.
- As with all trading strategies, there's risk involved. Always trade responsibly.
