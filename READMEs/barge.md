<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Barge

## Contents

Installation
- [Install Barge](#install-barge)

Reference: how to run barge with...
- [No agents](#barge-basic) - just ganache chain & predictoor contracts
- [One agent](#barge-one-agent) - eg trueval agent
- [All agents](#barge-all-agents) - predictoor, trader, trueval, dfbuyer


## Install Barge

- Pre-requisites: [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge
git checkout issue374-replace-pdr-components-with-pdr-backend # use this branch for now
export GANACHE_BLOCKTIME=5 # set ganache block time to 5 seconds, try increasing this value if barge is lagging
# (optional) Clean up previous Ocean-related containers
./cleanup.sh
```

The sections below describe different ways to run barge. They're for reference only; DO NOT run them right now. Each README will describe what to do.

## Barge Basic

Barge with basic Predictoor components is:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain

To run this, go to the barge console and:
```console
./start_ocean.sh --predictoor
```

When barge runs, it will auto-publish DT3 tokens. Currently this is {`BTC/TUSD`, Binance, 5min}, {`ETH/USDT`, Kraken, 5min} and {`XRP/USDT`, Binance, 5min}.

## Barge One Agent

Barge can run with any subset of the agents.

For example, to run barge with just trueval agent:
```console
./start_ocean.sh --predictoor --with-pdr-trueval
```

## Barge All Agents

To run with all agents:

```console
./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-trader --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

This will run all of the following at once:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain
- trueval agent
- trader agent
- predictoor agent
- dfbuyer agent

