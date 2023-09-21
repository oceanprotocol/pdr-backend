<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a DFBuyer Bot

This README describes how to run a dfbuyer bot (agent).

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
#run barge with all bots (agents) except dfbuyer
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-trader
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

# run dfbuyer bot (agent)
python pdr_backend/dfbuyer/main.py
```

There are other environment variables that you might want to set, such as the **weekly spending limit**. To get more information about them check out the [environment variables documentation](./envvars.md).

The bot will consume "WEEKLY_SPENDING_LIMIT" worth of assets each week. This amount is distributed equally among all DF eligible assets.

## Remote Testnet Usage

To run dfbuyer as azure container: see [azure-container-deployment.md](azure-container-deployment.md)

To get tokens from testnet: see [testnet-faucet.md](testnet-faucet.md)

## Remote Mainnet Usage

FIXME
