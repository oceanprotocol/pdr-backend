<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Barge

Barge is a Docker container to run a local Ganache network having Predictoor contracts and (optionally) local bots. This README describes how to install Barge, and provides reference on running it with various agents.

## Contents

Main:
- [Install Barge](#install-barge)

Reference: how to run barge with...
- [No agents](#barge-basic) - just ganache network & Predictoor contracts
- [One agent](#barge-one-agent) - eg trueval bot
- [All agents](#barge-all-agents) - predictoor, trader, trueval, dfbuyer bots


## Install Barge

**First, ensure pre-requisites:** [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)

**Then, install barge.** Open a new console and...

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

# Switch to predictoor branch of barge repo
git checkout predictoor

# Clean up previous Ocean-related dirs & containers (optional but recommended) 
rm -rf ~/.ocean
./cleanup.sh
docker system prune -a --volumes
```

**Then, get Docker running.** To run barge, you need the Docker engine running. Here's how:
- If you're on Linux: you're good, there's nothing extra to do.
- If you're on MacOS: 
  - via console: `open -a Docker`
  - or, via app: open Finder app, find Docker, click to open app. (You don't need to press "play" or anything else. The app being open is enough.)
  - ⚠️ MacOS may give Docker issues. [Here](macos.md) are workarounds.

Congrats! Barge is installed and ready to be run.

The sections below describe different ways to run barge. They're for reference only; DO NOT run them right now. Each README will describe what to do.

## Barge Basic

Barge with basic Predictoor components is:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain

To run this, go to the barge console and:
```console
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph
```

When barge runs, it will auto-publish DT3 tokens. Currently this is {`BTC/USDT`, Binance, 5min}, {`ETH/USDT`, Kraken, 5min} and {`XRP/USDT`, Binance, 5min}.

## Barge One Agent

Barge can run with any subset of the agents.

For example, to run barge with just trueval agent:
```console
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval
```

## Barge All Agents

To run with all agents:

```console
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-trader --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

This will run all of the following at once:
- local chain (ganache)
- predictoor-related smart contracts deployed to chain
- trueval agent
- trader agent
- predictoor agent
- dfbuyer agent

## Other READMEs

- [Parent predictoor README: predictoor.md](./predictoor.md)
- [Parent trader README: trader.md](./trader.md)
- [Root README](../README.md)
