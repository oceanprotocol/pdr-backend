<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a Trueval Bot

This README describes how to run a trueval bot.

## Install pdr-backend

Follow directions in [predictoor.md](predictoor.md)

## Local Network

First, [install barge](barge.md#install-barge).

Then, run barge. In barge console:
```console
#run barge with all bots (agents) except trueval
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-dfbuyer --with-pdr-predictoor --with-pdr-publisher --with-pdr-trader
```

Open a new console and:
```
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvar
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"
```

Copy [`ppss.yaml`](../ppss.yaml) into your own file `my_ppss.yaml` and change parameters as you see fit. The "trueval_ss" has parameters for this bot.

Then, run trueval bot. In console:
```console
pdr trueval my_ppss.yaml development
```


## Remote Usage

In the CLI, simply point to a different network:
```console
# run on testnet
pdr trueval my_ppss.yaml sapphire-testnet

# or, run on mainnet
pdr trueval my_ppss.yaml sapphire-mainnet
```


