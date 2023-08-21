<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Using Predictoor Subgraph

### Querying

You can query [subgraph](http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql) and see [this populated data PR](https://github.com/oceanprotocol/ocean-subgraph/pull/678) here for entities.

### Filtering

Here are additional envvars used to filter:

- PAIR_FILTER = if we do want to act upon only same pair, like  "BTC/USDT,ETH/USDT"
- TIMEFRAME_FILTER = if we do want to act upon only same timeframes, like  "5m,15m"
- SOURCE_FILTER = if we do want to act upon only same sources, like  "binance,kraken"
- OWNER_ADDRS = if we do want to act upon only same publishers, like  "0x123,0x124"
