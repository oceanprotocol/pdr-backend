<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Using Predictoor Subgraph

### Subgraph URLs

You can query an Ocean subgraph at one of:
- locally, at http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql
- Sapphire testnet, at https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph/graphql
- Sapphire mainnet, at (TBD)

### Typical query

For a general overview, here's a good one:
```text
query{
  predictContracts{
    id
    token{
      name
    }
    subscriptions(orderBy: expireTime orderDirection:desc first:10){
      user {
        id
      }
      expireTime
    }
    slots(orderBy: slot orderDirection:desc first:10){
      slot
      roundSumStakesUp
      roundSumStakes
      predictions(orderBy: timestamp orderDirection:desc){
        stake
        user {
          id
        }
        timestamp
        payout{
          payout
          predictedValue
          trueValue
        }
      }
      trueValues{
        trueValue
      }
    }
  } 
}
```
  

### Queries in pdr-backend agents

Agents like predictoor and trader do queries via [pdr_backend/util/subgraph.py](https://github.com/oceanprotocol/pdr-backend/edit/main/pdr_backend/util/subgraph.py).
- They call to a subgraph, at a given url, with a particular query
- and they may filter further

**Filters**. You can set these envvars to filter query results for agents.

- PAIR_FILTER = if we do want to act upon only same pair, like  "BTC/USDT,ETH/USDT"
- TIMEFRAME_FILTER = if we do want to act upon only same timeframes, like  "5m,15m"
- SOURCE_FILTER = if we do want to act upon only same sources, like  "binance,kraken"
- OWNER_ADDRS = if we do want to act upon only same publishers, like  "0x123,0x124"

### Appendix

- [ocean-subgraph repo](https://github.com/oceanprotocol/ocean-subgraph)
- [ocean-subgraph PR#678](https://github.com/oceanprotocol/ocean-subgraph/pull/678) lists full entities. (Things may have changed a bit since then)

