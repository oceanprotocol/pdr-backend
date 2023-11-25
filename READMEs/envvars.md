# Environment Variables (Envvars)

This page describes core envvars that are used by all agents, then envvars that are specific to each agent.

## Core Envvars

### Network Configuration

- **RPC_URL**: The RPC URL of the network.
  - Check out the [Sapphire Documentation](https://docs.oasis.io/dapp/sapphire/)
- **SUBGRAPH_URL**: The Ocean subgraph URL.
  - **TESTNET**: https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
  - **MAINNET**: https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
- **PRIVATE_KEY**: Private key of the wallet to use. **Must start with `0x`.**

### Filters

- **PAIR_FILTER**: Pairs to filter (comma-separated). Fetches all available pairs if empty. Example: `BTC/USDT,ETH/USDT`
- **TIMEFRAME_FILTER**: Timeframes to filter (comma-separated). Fetches all available timeframes if empty. Example: `5m,1h`
- **SOURCE_FILTER**: Price sources to filter (comma-separated). Fetches all available sources if empty. Example: `binance,kraken`
- **OWNER_ADDRS**: Addresses of contract deployers to filter (comma-separated). **Typically set to the address of the OPF deployer wallet.**
  - **TESTNET**: `0xe02a421dfc549336d47efee85699bd0a3da7d6ff`
  - **MAINNET**: `0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703`

## Agent-Specific Envvars

These are envvars that are specific to a given agent.

### Trueval Agent

- **SLEEP_TIME**: The pause duration (in seconds) between batch processing. Example: `5`
- **BATCH_SIZE**: Maximum number of truevals to handle in a batch. Example: `3`

### Trader Agent

- **TRADER_MIN_BUFFER**: Sets a threshold (in seconds) for trade decisions. Example: if value is `180` and there's 179 seconds left, no trade. If 181 seconds left, then trade.

### Predictoor Agent

- **SECONDS_TILL_EPOCH_END**: Determines how soon to start predicting. Example: if value is `60` then it will start submitting predictions 60 seconds before. It will continue to periodically submit predictions until there's no time left.
- **STAKE_AMOUNT**: The amount to stake in units of Eth.
  - For approach 1 stake amount is randomly determined this has no effect.
  - For approach 2 stake amount is determined by: `STAKE_AMOUNT * confidence` where confidence is between 0 and 1.
  - For approach 3 this is the stake amount.

### DFBuyer Agent

- **CONSUME_BATCH_SIZE**: Max number of consumes to process in a single transaction. Example: `10`
- **WEEKLY_SPENDING_LIMIT**: The target amount of tokens to be spent on consumes per week. Should be set to amount of Predictoor DF rewards for that week. Denominated in OCEAN. Example: `37000`
- **CONSUME_INTERVAL_SECONDS**: Time interval between each "buy", denominated in seconds. Example: `86400` (1 day) for it to consume daily. Daily is a good frequency, balancing tx cost with liveness.
