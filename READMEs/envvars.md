# Environment Variables

## Core Environment Variables

### Network Configuration

- **RPC_URL**: The RPC URL of the network.
  - Check out the [Sapphire Documentation](https://docs.oasis.io/dapp/sapphire/)
- **SUBGRAPH_URL**: The Ocean subgraph URL.
  - **TESTNET**: https://v4.subgraph.oasis-sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph/graphql
  - **MAINNET**: https://v4.subgraph.oasis-sapphire.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph/graphql
- **PRIVATE_KEY**: Private key of the wallet to use. **Must start with `0x`.**

### Filters

- **PAIR_FILTER**: Pairs to filter (comma-separated). Fetches all available pairs if empty. Example: `BTC/USDT,ETH/USDT`
- **TIMEFRAME_FILTER**: Timeframes to filter (comma-separated). Fetches all available timeframes if empty. Example: `5m,1h`
- **SOURCE_FILTER**: Price sources to filter (comma-separated). Fetches all available sources if empty. Example: `binance,kraken`
- **OWNER_ADDRS**: Addresses of contract deployers to filter (comma-separated). **Typically set to the address of the OPF deployer wallet.**
  - **TESTNET**: `0xe02a421dfc549336d47efee85699bd0a3da7d6ff`
  - **MAINNET**: Not deployed yet.

## Agent-Specific Environment Variables

### Trueval

- **SLEEP_TIME**: The pause duration (in seconds) between batch processing.
- **BATCH_SIZE**: Maximum number of truevals to handle in a batch.

### Trader

- **TRADER_MIN_BUFFER**: Sets a threshold (in seconds) for trade decisions. For example, if set to 180 and there's 179 seconds left, no trade. If 181, then trade.

### Predictoor

- **SECONDS_TILL_EPOCH_END**: Determines how soon to start predicting.

### DFBuyer

- **CONSUME_BATCH_SIZE**: Max number of consumes to process in a single transaction.
- **WEEKLY_SPENDING_LIMIT**: The target amount of tokens to be spent on consumes per week. Should be set to amount of Predictoor DF rewards for that week.
- **CONSUME_INTERVAL_SECONDS**: The frequency of consumes - in seconds. Ideally set it to 86400 (1 day).
