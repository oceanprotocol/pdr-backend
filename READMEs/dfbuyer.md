<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a DFBuyer Bot

This README describes how to run a dfbuyer bot.

## Install pdr-backend

Follow directions in [predictoor.md](predictoor.md)

## Local Network

First, [install barge](barge.md#install-barge).

Then, run barge. In barge console:

```console
#run barge with all bots (agents) except dfbuyer
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-trader
```

Open a new console and:

```console
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set envvar
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"
```

Copy [`ppss.yaml`](../ppss.yaml) into your own file `my_ppss.yaml` and change parameters as you see fit. The section "dfbuyer_ss" has parameters for this bot.

Then, run dfbuyer bot. In console:

```console
pdr dfbuyer my_ppss.yaml development
```

The bot will consume "weekly_spending_limit" worth of assets each week. This amount is distributed equally among all DF eligible assets. (This parameter is set in the yaml file.)

![flow](https://user-images.githubusercontent.com/25263018/269256707-566b9f5d-7e97-4549-b483-2a6700826769.png)

## Remote Usage

In the CLI, simply point to a different network:

```console
# run on testnet
pdr dfbuyer my_ppss.yaml sapphire-testnet

# or, run on mainnet
pdr dfbuyer my_ppss.yaml sapphire-mainnet
```
