<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a Trader Bot

This README describes how to run a trader bot (agent), to consume predictions, make trades, and earn $.

## Contents

- [Install](#install)
- [Local Usage](#local-usage)
- [Remote Testnet Usage](#remote-testnet-usage)
- [Remote Mainnet Usage](#remote-mainnet-usage)


## Install

First, [install pdr-backend](install.md).

Then, [install barge](barge.md#install-barge).

## Local Usage

In barge console:
```console
#run barge with all bots (agents) except trader
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

Open a new console and:
```
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://localhost:9000/subgraphs/name/oceanprotocol/ocean-subgraph"
#OR: export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"

# run trader bot (agent)
python pdr_backend/trader/main.py
```

There are other envvars that you might want to set, such as the owner addresses. The [envvars README](./envvars.md) has more info.

Relax & watch as the predictoor bot submits random predictions, trueval submits random true_vals for each epoch and trader signals trades.

You can query predictoor subgraph for detailed run info. See [subgraph.md](subgraph.md) for details.

The bot trades according to the `trade()` function in [`pdr_backend/trader/trade.py`](../pdr_backend/trader/trade.py). Its default strategy is simplistic; you need to customize it. The docstring at the top of `trade.py` provides more info.

## Remote Testnet Usage

To run trader as azure container: see [azure-container-deployment.md](azure-container-deployment.md)

To get tokens from testnet: see [testnet-faucet.md](testnet-faucet.md)

## Remote Mainnet Usage

To run trader as azure container: see [azure-container-deployment.md](azure-container-deployment.md)

Get [ROSE via this guide](get-rose-on-sapphire.md) and [OCEAN via this guide](get-ocean-on-sapphire.md).

## Final note

As with all trading strategies, there's risk involved. Always trade responsibly. Nothing in this README or related should be considered financial advice.
