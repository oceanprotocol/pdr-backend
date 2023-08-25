"""
The `trade()` function below defines your trading strategy().

Its default strategy is simplistic: it only prints the incoming signal.

Therefore you _need_ to customize it. Here are details, to equip you to do this.

`trade()` is called when there's a signal for a specific trading pair, like ETH-USDT.

`trade()` accepts two inbound arguments, `topic` and `direction`.
As a trader, your `trade()` implementation uses them for trading decisions.

1. `topic` is a `dict` with info about the trading pair:
  - `name` - The name of the trading pair, e.g., "ETH-USDT".
  - `symbol` - Symbol of the trading pair.
  - `base` - Base currency of the trading pair.
  - `quote` - Quote currency of the trading pair.
  - `source` - Source exchange or platform.
  - `timeframe` - Timeframe for the trade signal, e.g., "5m" for 5 minutes.

2. `direction` is a `tuple` of `(stake_up, total_stake)`.
  - `stake_up` is the amount staked by predictoors betting on price going up (stake_up)
  - `total_stake` is the total amount staked by all predictoors.
"""


def trade(topic, direction):
    """Given a direction for a topic, let's trade
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
        f" {topic['name']} (contract {topic['address']}) "
        f"has a new prediction: {direction}.  Let's buy or sell"
    )
    # Do your things here
    # ...
