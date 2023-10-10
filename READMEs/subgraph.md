<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Using Predictoor Subgraph

### Subgraph URLs

You can query an Ocean subgraph at one of the following:

Local (= `$SUBGRAPH_URL`):
  - http://localhost:9000/subgraphs/name/oceanprotocol/ocean-subgraph
  - OR http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph

Remote:
- Sapphire testnet, at https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
- Sapphire mainnet, at https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph

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

**Filters**, You can set some envvars to filter query results for agents. Check out the [envvar documentation](./envvars.md#filters) to learn more about these filters and how to set them.

### Appendix

- [ocean-subgraph repo](https://github.com/oceanprotocol/ocean-subgraph)
- [ocean-subgraph PR#678](https://github.com/oceanprotocol/ocean-subgraph/pull/678) lists full entities. (Things may have changed a bit since then)
