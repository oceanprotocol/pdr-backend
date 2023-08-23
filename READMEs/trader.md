<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Traders

This is for traders - people who are running `trader` agents that buy aggregated predictions, then trade.

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
#run barge with all agents except trader
./start_ocean.sh --predictoor --with-thegraph --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

Open a new console and:
```
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PRIVATE_KEY="0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"

# run trader agent
python pdr_backend/trader/main.py
```

Relax & watch as the predictoor agent submits random predictions, trueval submits random true_vals for each epoch and trader signals trades.

You can query predictoor subgraph for detailed run info. See [subgraph.md](subgraph.md) for details.

The agent trades according to the `trade()` function in [`pdr_backend/trader/trade.py`](../pdr_backend/trader/trade.py). Its default strategy is simplistic; you need to customize it. The docstring at the top of `trade.py` provides more info.

## Remote Testnet Usage

To run predictoor as azure container: see [azure-container-deployment.md](azure-container-deployment.md)

To get tokens from testnet: see [testnet-faucet.md](testnet-faucet.md)

## Remote Mainnet Usage

FIXME

## Final note

As with all trading strategies, there's risk involved. Always trade responsibly. Nothing in this README or related should be considered financial advice.
