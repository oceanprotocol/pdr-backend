<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Publishers

This is for publishers to publish new prediction feeds as data assets (data NFT & datatoken). Typically this is done by the Ocean core team.

## Install pdr-backend

Follow directions in [predictoor.md](predictoor.md)

## Local Network

First, [install barge](barge.md#install-barge)

Then, run barge. In barge console:
```console
# Run barge with just predictoor contracts, queryable, but no agents
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph
```

Open a new console and:
```console
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvars - note that publisher needs >>1 private keys
export PREDICTOOR_PRIVATE_KEY=<YOUR_PRIVATE_KEY>
export PREDICTOOR2_PRIVATE_KEY=<YOUR_PRIVATE_KEY>
export PREDICTOOR3_PRIVATE_KEY=<YOUR_PRIVATE_KEY>
export TRADER_PRIVATE_KEY=<YOUR_PRIVATE_KEY>
export DFBUYER_PRIVATE_KEY=<YOUR_PRIVATE_KEY>
export PDR_WEBSOCKET_KEY=<YOUR_PRIVATE_KEY>
export PDR_MM_USER=<YOUR_PRIVATE_KEY>
"""

Copy [`ppss.yaml`](../ppss.yaml) into your own file `my_ppss.yaml` and change parameters as you see fit. The section "publisher_ss" has parameters for this bot.

Then, run publisher bot. In console:
```console
pdr publisher my_ppss.yaml development
```


## Remote Usage

In the CLI, simply point to a different network:
```console
# run on testnet
pdr publisher my_ppss.yaml sapphire-testnet

# or, run on mainnet
pdr publisher my_ppss.yaml sapphire-mainnet
```
