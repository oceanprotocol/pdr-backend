<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Publishers

This is for publishers to publish new prediction feeds as data assets (data NFT & datatoken). Typically this is done by the Ocean core team.

## Contents

- [Install](#install)
- [Local Usage](#local-usage)
- [Remote Testnet Usage](#remote-testnet-usage)
- [Remote Mainnet Usage](#remote-mainnet-usage)

## Install

First, [install pdr-backend](install.md).

Then, [install barge](barge.md#install-barge).

## Local Usage

### Local Usage: Testing

In barge console:
```console
# Run barge with just predictoor contracts, queryable, but no agents
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph
```

Open a new console and:
```console
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars - note that publisher needs WAY more private keys than others
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export RPC_URL=http://127.0.0.1:8545
export SUBGRAPH_URL="http://localhost:9000/subgraphs/name/oceanprotocol/ocean-subgraph"
#OR: export SUBGRAPH_URL="http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
export PREDICTOOR_PRIVATE_KEY = "<your key>"
export PREDICTOOR2_PRIVATE_KEY = "<your key>"
export PREDICTOOR3_PRIVATE_KEY = "<your key>"
export TRADER_PRIVATE_KEY = "<your key>"
export DFBUYER_PRIVATE_KEY = "<your key>"
export PDR_WEBSOCKET_KEY = "<your key>"
export PDR_MM_USER = "<your key>"
"""

# publish! main.py & publish.py do all the work
python pdr_backend/publisher/main.py
```

## Remote Testnet Usage

FIXME

## Remote Mainnet Usage

FIXME

