<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Using Predictoor Subgraph

### Subgraph URLs

You can query an Ocean subgraph at one of the following:

The subgraph url for each network is in the ppss yaml under "subgraph url".

Typically, these are something like:

- Local (barge)
  - http://localhost:9000/subgraphs/name/oceanprotocol/ocean-subgraph
  - OR http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph
- Sapphire testnet
  - https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
- Sapphire mainnet
  - https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph

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

Agents like predictoor and trader do queries via [pdr_backend/util/subgraph.py](https://github.com/oceanprotocol/pdr-backend/blob/main/pdr_backend/util/subgraph.py).

- They call to a subgraph, at a given url, with a particular query
- and they may filter further

### Appendix

- [ocean-subgraph repo](https://github.com/oceanprotocol/ocean-subgraph)
