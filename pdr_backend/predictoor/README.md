# Predictoor

This is for predictoors - people who are running `predictoor` agents to submit individual predictions.

## Flow

- Fetches a list of Predictoor contracts from subgraph and filters them based on the filters set.
- Monitors each contract for epoch changes.
- When a value can be predicted, the `predict_function` in predict.py is called.

## How to Customize

The heart of Predictoor lies in the `predict_function()` inside predict.py. 

### predict_function

The function is called with 2 arguments:

- topic: Information about the trading pair.
- timestamp: Timestamp of the prediction.

The function should return:

- predicted_value: Boolean, indicating the prediction direction (True for up, False for down).
- predicted_confidence: Integer between 1 and 100. Represents the confidence level in the prediction.
- stake_amount: Amount of tokens to stake for the prediction.

By default, `predict_function` uses random values for predictions. You need to customize it and implement your own strategy.

### Topic Object

The topic object has all the details about the pair:

- `name` - The name of the trading pair, e.g., "ETH-USDT".
- `symbol` - Symbol of the trading pair.
- `base` - Base currency of the trading pair.
- `quote` - Quote currency of the trading pair.
- `source` - Source exchange or platform.
- `timeframe` - Timeframe for the trade signal, e.g., "5m" for 5 minutes.

### Filters

Set the following environment variables to filter the contracts the predictoor agent will predict on.

- PAIR_FILTER = if we do want to act upon only same pair, like  "BTC/USDT,ETH/USDT"
- TIMEFRAME_FILTER = if we do want to act upon only same timeframes, like  "5m,15m"
- SOURCE_FILTER = if we do want to act upon only same sources, like  "binance,kraken"
- OWNER_ADDRS = if we do want to act upon only same publishers, like  "0x123,0x124"

### `SECONDS_TILL_EPOCH_END`
Adjust the environment variable `SECONDS_TILL_EPOCH_END` to control how many seconds in advance of the epoch ending you want the prediction process to start. A predictoor can submit multiple predictions, however, only the final submission made before the deadline is considered valid.

To clarify further: if this value is set to 60, the predictoor will be asked to predict in every block during the last 60 seconds before the epoch concludes.

### How to run

First, [install pdr-backend](install.md).

FIXME (add a readme to explain env vars)

Setup env vars depeding on where you're going to run the agent (local/testnet/mainnet)

Run `predictoor` agent by:

```shell
python3 pdr_backend/predictoor/main.py
```